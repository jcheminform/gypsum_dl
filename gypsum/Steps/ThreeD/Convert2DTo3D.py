"""A module to so the 2D to 3D conversion, though the actual code for that
conversion is in MyMol.MyMol.make_first_3d_conf_no_min()"""

import __future__
import copy

import gypsum.Parallelizer as Parallelizer
import gypsum.Utils as Utils
import gypsum.ChemUtils as ChemUtils

try:
    from rdkit import Chem
    from rdkit.Chem import AllChem
except:
    Utils.log("You need to install rdkit and its dependencies.")
    raise ImportError("You need to install rdkit and its dependencies.")

def convert_2d_to_3d(contnrs, max_variants_per_compound, thoroughness, num_procs, multithread_mode, parallelizer_obj):
    """Converts the 1D smiles strings into 3D small-molecule models.

    :param contnrs: A list of containers (MolContainer.MolContainer).
    :type contnrs: list
    :param max_variants_per_compound: [description] JDD: Figure out.
    :type max_variants_per_compound: int
    :param thoroughness: [description] JDD: Figure out.
    :type thoroughness: int
    :param num_procs: The number of processors to use.
    :type num_procs: int
    :param multithread_mode: The multithred mode to use.
    :type multithread_mode: string
    :param parallelizer_obj: The Parallelizer object.
    :type parallelizer_obj: Parallelizer.Parallelizer
    """

    Utils.log("Converting all molecules to 3D structures.")

    # Make the inputs to pass to the parallelizer.
    params = []
    for contnr in contnrs:
        for mol in contnr.mols:
            params.append(tuple([mol]))
    params = tuple(params)

    # Run the parallelizer
    tmp = parallelizer_obj.run(params, parallel_make_3d, num_procs, multithread_mode)

    # Remove and Nones from the output, which represent failed molecules.
    clear = Parallelizer.strip_none(tmp)

    # Keep only the top few compound variants in each container, to prevent a
    # combinatorial explosion.
    ChemUtils.bst_for_each_contnr_no_opt(contnrs, clear, max_variants_per_compound, thoroughness, False)

def parallel_make_3d(mol):
    """Does the 2D to 3D conversion. Meant to run within parallelizer.

    :param mol: The molecule to be converted.
    :type mol: MyMol.MyMol
    :return: A MyMol.MyMol object with the 3D coordinates inside, or None if
       it fails.
    :rtype: MyMol.MyMol | None
    """

    # Initially assume you won't show an error message.
    show_error_msg = False

    if mol.rdkit_mol is None:
        # The rdkit mol is None. Something's gone wrong. Show an error
        # message.
        show_error_msg = True
    else:
        # Check if it has strange substructures.
        if mol.remove_bizarre_substruc() == False:
            # Perform the conversion.
            mol.make_first_3d_conf_no_min()

            # If there are some conformations, make note of that in the
            # genealogy record.
            if len(mol.conformers) > 0:
                mol.genealogy.append(
                    mol.smiles(True) + " (3D coordinates assigned)"
                )
                return mol
            else:
                # No conformers? Show an error. Something's gone wrong.
                show_error_msg = True

    if show_error_msg:
        # Something's gone wrong, so show this error.
        Utils.log(
            "\tWarning: Could not generate 3D geometry for " +
            str(mol.smiles()) + " (" + mol.name + "). Molecule " +
            "discarded."
        )

    # If you get here, something's gone wrong...
    return None
