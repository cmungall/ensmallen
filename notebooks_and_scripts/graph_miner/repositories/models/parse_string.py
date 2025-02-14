"""Submodule with methods to parse and standardize STRING graphs."""
import pandas as pd


def parse_string_fasta(path: str) -> pd.DataFrame:
    """Return dataframe with aminoacid fasta sequences from given path.

    Parameters
    -----------------------
    path: str
        Path to the fasta file to load.
    """
    current_protein = current_sequence = ""
    proteins = []
    sequences = []
    with open(path, "r") as f:
        for line in f.readlines():
            line = line.strip()
            if line.startswith(">"):
                if len(current_sequence) != 0:
                    proteins.append(current_protein)
                    sequences.append(current_sequence)
                current_protein = line[1:]
                current_sequence = ""
            else:
                current_sequence += line

    return pd.DataFrame({
        # We follow the notation from other STRING PPI graph files.
        "#string_protein_id": proteins,
        "sequence": sequences,
    }).set_index("#string_protein_id")


def group_annotate_string_node_list(path: str) -> pd.DataFrame:
    """Return file grouped by protein node name.

    Parameters
    -----------------------
    path: str
        Path to the annotated protein node list file to load.
    """
    df: pd.DataFrame = pd.read_csv(path, sep="\t")

    df.drop(columns="category", inplace=True)

    return df.groupby("#string_protein_id")\
        .agg(lambda x: "|".join(sorted(set(x))))



def load_string_info_node_list(path: str) -> pd.DataFrame:
    """Return loaded STRING node list with informations.

    Parameters
    -----------------------
    path: str
        Path to the protein node list with informations.
    """
    return pd.read_csv(path, sep="\t", index_col=0)


def create_species_tree_node_and_edge_list(
    tree_path: str,
    tree_metadata_path: str,
    node_list_path: str,
    edge_list_path: str
):
    """Create the node and edge lists for the species tree at given path.

    Parameters
    -------------------
    tree_path: str
        The path from where to load the tree data.
    tree_metadata_path: str
        The path from where to load the tree metadata.
    node_list_path: str
        The path where to store the tree node list.
    edge_list_path: str
        The path where to store the tree edge list.
    """
    tree = pd.read_csv(tree_path, sep="\t", index_col=0)
    metadata = pd.read_csv(tree_metadata_path, sep="\t", index_col=0)

    # Imputing the missing domains in the Species Tree.
    tree.loc[metadata.index, "domain"] = metadata.domain
    tree.loc[tree.parent_taxon_id==1, "domain"] = "Ancestral"
    tree.loc[tree.domain == "Eukaryotes", "domain"] = "Eukaryota"
    tree = pd.concat(
        [tree, pd.DataFrame(dict(parent_taxon_id=1, taxon_name="LUCA"), index=[1])]
    )

    while tree.domain.isna().any():
        child_nodes = tree[tree.loc[tree.parent_taxon_id].domain.isna().values & tree.domain.notna().values]    
        tree.loc[child_nodes.parent_taxon_id, "domain"] = child_nodes.domain.values
    
    # We drop the temporary node index 1
    tree.drop(index=1, inplace=True)

    # Making taxon names unique, so that corner cases
    # such as `Drosophila Drosophila` can be handled.
    tree.loc[tree.duplicated("taxon_name"), "taxon_name"] = [
        "{}.{}".format(taxon_name, index)
        for index, taxon_name in tree.loc[tree.duplicated("taxon_name"), "taxon_name"].iteritems()
    ]
    
    # Writing the node list
    node_list = tree[["taxon_name", "domain"]]
    node_list.to_csv(node_list_path, sep="\t", index=False)

    # We drop edges from the root node to LUCA
    tree.drop(
        index=tree[tree.parent_taxon_id == 1].index[0],
        inplace=True
    )

    # Writing the edge list
    pd.DataFrame({
        "sources": node_list.loc[tree.parent_taxon_id].taxon_name.values,
        "destinations": node_list.loc[tree.index].taxon_name.values,
        "domain": tree.domain.values
    }).to_csv(edge_list_path, sep="\t", index=False)


def build_string_graph_node_list(
    sequence_path: str,
    enrichment_path: str,
    info_path: str,
    node_list_path: str
):
    """Processes string data into node list.

    Parameters
    ----------------------
    sequence_path: str
        File from where to load sequence data.
    enrichment_path: str
        File from where to load enrichment data.
    info_path: str
        File from where to load info data.
    node_list_path: str
        Path where to write the resulting TSV.
    """

    fasta_df = parse_string_fasta(sequence_path)
    enrichment_df = group_annotate_string_node_list(enrichment_path)
    info_df = load_string_info_node_list(info_path)

    merged_df = pd.concat(
        (info_df, enrichment_df, fasta_df),
        axis=1
    )

    merged_df.to_csv(
        node_list_path,
        sep="\t",
        index=True,
        header=True
    )


def build_string_cluster_graph_node_and_edge_list(
    cluster_info_path: str,
    cluster_tree_path: str,
    cluster_to_proteins_path: str,
    sequence_path: str,
    enrichment_path: str,
    info_path: str,
    node_list_path: str,
    edge_list_path: str,
):
    """Build labeled edge and node list for cluster graphs.
    
    Parameters
    -----------------------
    cluster_info_path: str
        Path from where to load the cluster node list informations.
    cluster_tree_path: str
        Path from where to load the cluster to cluster edge list.
    cluster_to_proteins_path: str
        Path from where to load the cluster to protein edge list.
    sequence_path: str
        File from where to load sequence data.
    enrichment_path: str
        File from where to load enrichment data.
    info_path: str
        File from where to load info data.
    target_path: str
        Path where to write the resulting node list TSV.
    """
    build_string_graph_node_list(
        sequence_path=sequence_path,
        enrichment_path=enrichment_path,
        info_path=info_path,
        node_list_path=node_list_path,
    )
    cluster_only_node_list = pd.read_csv(cluster_info_path, sep="\t")
    cluster_only_node_list["term"] = "Cluster"
    cluster_only_node_list.rename(
        columns={
            "best_described_by": "description",
            "cluster_id": "node_name"
        },
        inplace=True
    )
    string_only_node_list = pd.read_csv(node_list_path, sep="\t")
    string_only_node_list.rename(
        columns={
            "#string_protein_id": "node_name"
        },
        inplace=True
    )
    node_list = pd.concat((cluster_only_node_list, string_only_node_list), axis=0)
    node_list.to_csv(node_list_path, sep="\t")

    cluster_tree_df = pd.read_csv(cluster_tree_path, sep="\t")
    cluster_to_proteins_df = pd.read_csv(cluster_to_proteins_path, sep="\t")

    cluster_tree_df.rename(
        columns={
            "child_cluster_id": "source",
            "parent_cluster_id": "destination",
        },
        inplace=True
    )

    cluster_to_proteins_df.rename(
        columns={
            "cluster_id": "source",
            "protein_id": "destination",
        },
        inplace=True
    )

    edge_list = pd.concat((
        cluster_tree_df[["source", "destination"]],
        cluster_to_proteins_df[["source", "destination"]],
    ), axis=0)

    edge_list.to_csv(edge_list_path, sep="\t", index=False)