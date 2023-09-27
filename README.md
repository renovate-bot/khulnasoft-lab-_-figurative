# :warning: Project is in Maintenance Mode :warning:

This project is no longer internally developed and maintained. However, we are happy to review and accept small, well-written pull requests by the community. We will only consider bug fixes and minor enhancements.

Any new or currently open issues and discussions shall be answered and supported by the community.

# Figurative
<p align="center">
  <img src="https://raw.githubusercontent.com/khulnasoft-lab/figurative/master/docs/images/figurative.png" width="256" title="Figurative">
</p>
<br />


[![Build Status](https://img.shields.io/github/actions/workflow/status/khulnasoft-lab/figurative/ci.yml?branch=master)](https://github.com/khulnasoft-lab/figurative/actions?query=workflow%3ACI)
[![Coverage Status](https://coveralls.io/repos/github/khulnasoft-lab/figurative/badge.svg)](https://coveralls.io/github/khulnasoft-lab/figurative)
[![PyPI Version](https://badge.fury.io/py/figurative.svg)](https://badge.fury.io/py/figurative)
[![Slack Status](https://slack.empirehacking.nyc/badge.svg)](https://slack.empirehacking.nyc)
[![Documentation Status](https://readthedocs.org/projects/figurative/badge/?version=latest)](http://figurative.readthedocs.io/en/latest/?badge=latest)
[![Example Status](https://img.shields.io/github/actions/workflow/status/khulnasoft-lab/figurative-examples/ci.yml?branch=master)](https://github.com/khulnasoft-lab/figurative-examples/actions?query=workflow%3ACI)
[![LGTM Total Alerts](https://img.shields.io/lgtm/alerts/g/khulnasoft-lab/figurative.svg?logo=lgtm&logoWidth=18)](https://lgtm.com/projects/g/khulnasoft-lab/figurative/alerts/)



Figurative is a symbolic execution tool for the analysis of smart contracts and binaries.

## Features

- **Program Exploration**: Figurative can execute a program with symbolic inputs and explore all the possible states it can reach
- **Input Generation**: Figurative can automatically produce concrete inputs that result in a given program state
- **Error Discovery**: Figurative can detect crashes and other failure cases in binaries and smart contracts
- **Instrumentation**: Figurative provides fine-grained control of state exploration via event callbacks and instruction hooks
- **Programmatic Interface**: Figurative exposes programmatic access to its analysis engine via a Python API

Figurative can analyze the following types of programs:

- Ethereum smart contracts (EVM bytecode)
- Linux ELF binaries (x86, x86_64, aarch64, and ARMv7)
- WASM Modules

## Installation

> Note: We recommend installing Figurative in a [virtual environment](https://packaging.python.org/guides/installing-using-pip-and-virtual-environments/#installing-virtualenv)
 to prevent conflicts with other projects or packages

Option 1: Installing from PyPI:

```bash
pip install figurative
```

Option 2: Installing from PyPI, with extra dependencies needed to execute native binaries:

```bash
pip install "figurative[native]"
```

Option 3: Installing a nightly development build:

```bash
pip install --pre "figurative[native]"
```

Option 4: Installing from the `master` branch:

```bash
git clone https://github.com/khulnasoft-lab/figurative.git
cd figurative
pip install -e ".[native]"
```

Option 5: Install via Docker:

```bash
docker pull khulnasoft-lab/figurative
```

Once installed, the `figurative` CLI tool and Python API will be available.

For a development installation, see our [wiki](https://github.com/khulnasoft-lab/figurative/wiki/Hacking-on-Figurative).

## Usage

### CLI

Figurative has a command line interface which can perform a basic symbolic analysis of a binary or smart contract. 
Analysis results will be placed into a workspace directory beginning with `mcore_`. For information about the workspace, see the [wiki](https://github.com/khulnasoft-lab/figurative/wiki/What's-in-the-workspace%3F).

#### EVM
Figurative CLI automatically detects you are trying to test a contract if (for ex.)
 the contract has a `.sol` or a `.vy` extension. See a [demo](https://asciinema.org/a/154012).
<details>
  <summary>Click to expand:</summary>
  
```bash
$ figurative examples/evm/umd_example.sol 
 [9921] m.main:INFO: Registered plugins: DetectUninitializedMemory, DetectReentrancySimple, DetectExternalCallAndLeak, ...
 [9921] m.e.figurative:INFO: Starting symbolic create contract
 [9921] m.e.figurative:INFO: Starting symbolic transaction: 0
 [9921] m.e.figurative:INFO: 4 alive states, 6 terminated states
 [9921] m.e.figurative:INFO: Starting symbolic transaction: 1
 [9921] m.e.figurative:INFO: 16 alive states, 22 terminated states
[13761] m.c.figurative:INFO: Generated testcase No. 0 - STOP(3 txs)
[13754] m.c.figurative:INFO: Generated testcase No. 1 - STOP(3 txs)
...
[13743] m.c.figurative:INFO: Generated testcase No. 36 - THROW(3 txs)
[13740] m.c.figurative:INFO: Generated testcase No. 37 - THROW(3 txs)
[9921] m.c.figurative:INFO: Results in ~/figurative/mcore_gsncmlgx
```
</details>

##### Figurative-verifier

An alternative CLI tool is provided that simplifies contract testing and 
allows writing properties methods in the same high-level language the contract uses.
Checkout figurative-verifier [documentation](http://figurative.readthedocs.io/en/latest/verifier.html).
See a [demo](https://asciinema.org/a/xd0XYe6EqHCibae0RP6c7sJVE)

#### Native
<details>
  <summary>Click to expand:</summary>
  
```bash
$ figurative examples/linux/basic
[9507] m.n.figurative:INFO: Loading program examples/linux/basic
[9507] m.c.figurative:INFO: Generated testcase No. 0 - Program finished with exit status: 0
[9507] m.c.figurative:INFO: Generated testcase No. 1 - Program finished with exit status: 0
[9507] m.c.figurative:INFO: Results in ~/figurative/mcore_7u7hgfay
[9507] m.n.figurative:INFO: Total time: 2.8029580116271973
```
</details>


### API

Figurative provides a Python programming interface which can be used to implement powerful custom analyses.

#### EVM
For Ethereum smart contracts, the API can be used for detailed verification of arbitrary contract properties. Users can set the starting conditions, 
execute symbolic transactions, and then review discovered states to ensure invariants for a contract hold.
<details>
  <summary>Click to expand:</summary>
  
```python
from figurative.ethereum import FigurativeEVM
contract_src="""
contract Adder {
    function incremented(uint value) public returns (uint){
        if (value == 1)
            revert();
        return value + 1;
    }
}
"""
m = FigurativeEVM()

user_account = m.create_account(balance=10000000)
contract_account = m.solidity_create_contract(contract_src,
                                              owner=user_account,
                                              balance=0)
value = m.make_symbolic_value()

contract_account.incremented(value)

for state in m.ready_states:
    print("can value be 1? {}".format(state.can_be_true(value == 1)))
    print("can value be 200? {}".format(state.can_be_true(value == 200)))
```
</details>

#### Native
It is also possible to use the API to create custom analysis tools for Linux binaries. Tailoring the initial state helps avoid state explosion
problems that commonly occur when using the CLI. 

<details>
  <summary>Click to expand:</summary>
  
```python
# example Figurative script
from figurative.native import Figurative

m = Figurative.linux('./example')

@m.hook(0x400ca0)
def hook(state):
  cpu = state.cpu
  print('eax', cpu.EAX)
  print(cpu.read_int(cpu.ESP))

  m.kill()  # tell Figurative to stop

m.run()
```
</details>


#### WASM
Figurative can also evaluate WebAssembly functions over symbolic inputs for property validation or general analysis. 

<details>
  <summary>Click to expand:</summary>
  
```python
from figurative.wasm import FigurativeWASM

m = FigurativeWASM("collatz.wasm")

def arg_gen(state):
    # Generate a symbolic argument to pass to the collatz function.
    # Possible values: 4, 6, 8
    arg = state.new_symbolic_value(32, "collatz_arg")
    state.constrain(arg > 3)
    state.constrain(arg < 9)
    state.constrain(arg % 2 == 0)
    return [arg]


# Run the collatz function with the given argument generator.
m.collatz(arg_gen)

# Manually collect return values
# Prints 2, 3, 8
for idx, val_list in enumerate(m.collect_returns()):
    print("State", idx, "::", val_list[0])
```
</details>

## Requirements
* Figurative requires Python 3.7 or greater 
* Figurative officially supports the latest LTS version of Ubuntu provided by Github Actions
  * Figurative has experimental support for EVM and WASM (but not native Linux binaries) on MacOS 
* We recommend running with increased stack size. This can be done by running `ulimit -s 100000` or by passing `--ulimit stack=100000000:100000000` to `docker run`

### Compiling Smart Contracts
* Ethereum smart contract analysis requires the [`solc`](https://github.com/ethereum/solidity) program in your `$PATH`.
* Figurative uses [crytic-compile](https://github.com/crytic/crytic-compile) to build smart contracts. If you're having compilation issues, consider running 
`crytic-compile` on your code directly to make it easier to identify any issues. 
* We're still in the process of implementing full support for the EVM Istanbul instruction semantics, so certain opcodes may not be supported.
In a pinch, you can try compiling with Solidity 0.4.x to avoid generating those instructions. 

## Using a different solver (Yices, Z3, CVC4)
Figurative relies on an external solver supporting smtlib2. Currently Z3, Yices and CVC4 are supported and can be selected via command-line or configuration settings.
If Yices is available, Figurative will use it by default. If not, it will fall back to Z3 or CVC4. If you want to manually choose which solver to use, you can do so like this:
```figurative --smt.solver Z3```
### Installing CVC4
For more details go to https://cvc4.github.io/. Otherwise, just get the binary and use it.

        sudo wget -O /usr/bin/cvc4 https://github.com/CVC4/CVC4/releases/download/1.7/cvc4-1.7-x86_64-linux-opt
        sudo chmod +x /usr/bin/cvc4

### Installing Yices
Yices is incredibly fast. More details here https://yices.csl.sri.com/

        sudo add-apt-repository ppa:sri-csl/formal-methods
        sudo apt-get update
        sudo apt-get install yices2

## Getting Help

Feel free to stop by our #figurative slack channel in [Empire Hacking](https://slack.empirehacking.nyc/) for help using or extending Figurative.

Documentation is available in several places:

  * The [wiki](https://github.com/khulnasoft-lab/figurative/wiki) contains information about getting started with Figurative and contributing

  * The [API reference](http://figurative.readthedocs.io/en/latest/) has more thorough and in-depth documentation on our API
    
  * The [examples](examples) directory has some small examples that showcase API features

  * The [figurative-examples](https://github.com/khulnasoft-lab/figurative-examples) repository has some more involved examples, including some real CTF problems

If you'd like to file a bug report or feature request, please use our [issues](https://github.com/khulnasoft-lab/figurative/issues/choose) page. 

For questions and clarifications, please visit the [discussion](https://github.com/khulnasoft-lab/figurative/discussions) page.

## License

Figurative is licensed and distributed under the AGPLv3 license. [Contact us](mailto:opensource@khulnasoft-lab.com) if you're looking for an exception to the terms.

## Publications
- [Figurative: A User-Friendly Symbolic Execution Framework for Binaries and Smart Contracts](https://arxiv.org/abs/1907.03890), Mark Mossberg, Felipe Manzano, Eric Hennenfent, Alex Groce, Gustavo Grieco, Josselin Feist, Trent Brunson, Artem Dinaburg - ASE 19

If you are using Figurative in academic work, consider applying to the [Crytic $10k Research Prize](https://blog.khulnasoft-lab.com/2019/11/13/announcing-the-crytic-10k-research-prize/).

## Demo Video from ASE 2019
[![Brief Figurative demo video](https://img.youtube.com/vi/o6pmBJZpKAc/1.jpg)](https://youtu.be/o6pmBJZpKAc)

## Tool Integrations 

- [MATE: Merged Analysis To prevent Exploits](https://github.com/GaloisInc/MATE)
  * [Mantiserve:](https://galoisinc.github.io/MATE/mantiserve.html) REST API interaction with Figurative to start, kill, and check Figurative instance
  * [Dwarfcore:](https://galoisinc.github.io/MATE/dwarfcore.html) Plugins and detectors for use within Mantiserve engine during exploration 
  * [Under-constrained symbolic execution](https://github.com/GaloisInc/MATE/blob/main/doc/under-constrained-figurative.rst) Interface for symbolically exploring single functions with Figurative
