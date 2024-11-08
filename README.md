# ltl-learning

This project implements the algorithm proposed by Neider & Gavran in their 2018 article [Learning Temporal Properties](https://arxiv.org/abs/1806.03953) using Python3 and the Z3 SAT solver (more specifically its python bindings z3py), allowing to learn an LTL Formula from traces containing ultimately periodic words.

This tool supports the traces being input as JSON files, a format easily readable both by humans and machines, allowing easy setup of simulation data.


## Usage

For an example of an input trace, see the [mutex](./tests/fixtures/mutex.json) file.
For an example of how to use the tool programmatically, please refer to the [tests](./tests/) folder.

In order to use the tool from command line, you have to launch it using the `python` command:

```shell
python -m ltl_learner -f INPUT_FILE.json [-k MAX_VARIABLES_FOR_LTL] [-o OPERATORS.json]
```
