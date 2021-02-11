# Glow
More information about 
A simple git extension to use [git flow branching model](http://nvie.com/posts/a-successful-git-branching-model/). automatically with Github 
and [semver](https://semver.org/) to tags your releases and hotfixes.

![Screenshot](./images/screenshot-20210211-141619.png)

## Requirements

- git
- Python 3.7+

## How to setup

Generate a Github token

```shell
pip install git-glow
# OR
pip install .
```

## Usage

To use this command, just type ```git glow``` in a git repository
with a **develop** and **master** branch.

### Feature

```shell
git glow start feature 1234
git glow review feature 1234
git glow finish feature 1234
```

### Release

```shell
git glow start release
git glow review release
git glow finish release
```

### Hotfix

```shell
git glow start hotfix
git glow review hotfix
git glow finish hotfix
```
