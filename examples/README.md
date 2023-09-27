# Figurative Examples

## Quickstart

Install and try Figurative in a few shell commands:

```bash
# (Recommended) Create a virtual environment for Figurative
virtualenv -p `which python3` mcenv
source mcenv/bin/activate

# Install Figurative and its dependencies
pip install figurative[native]

# Download the examples
git clone https://github.com/khulnasoft-lab/figurative.git && cd figurative/examples/linux

# Build the examples
make

# Use the Figurative CLI
figurative basic
cat mcore_*/*0.stdin | ./basic
cat mcore_*/*1.stdin | ./basic

# Use the Figurative API
cd ../script
python count_instructions.py ../linux/helloworld
```

You can also use Docker to quickly install and try Figurative:

```bash
# Run container with a shared examples/ directory
# Note that `--rm` will make the container be deleted if you exit it
# (if you want to persist data from the container, use docker volumes)
# (we need to increase maximum stack size, so we use ulimit for that)
$ docker run --rm -it --ulimit stack=100000000:100000000 khulnasoft-lab/figurative bash

# Change to examples directory
figurative@8d456f662d0f:~$ cd figurative/examples/linux/

# Build the examples
figurative@8d456f662d0f:~/figurative/examples/linux$ make

# Use the Figurative CLI
figurative@8d456f662d0f:~/figurative/examples/linux$ figurative basic


figurative@8d456f662d0f:~/figurative/examples/linux$ cat mcore_*/*0.stdin | ./basic
figurative@8d456f662d0f:~/figurative/examples/linux$ cat mcore_*/*1.stdin | ./basic

# Use the Figurative API
figurative@8d456f662d0f:~/figurative/examples/linux$ cd ../script
figurative@8d456f662d0f:~/figurative/examples/script$ python3.7 count_instructions.py ../linux/helloworld
```
