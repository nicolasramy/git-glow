# git-glow
A new git extension to use git flow branching model automatically on Github

## Requirements

- git
- Python 3.7+

In a git repository with a **develop** and **main** branch.

More information about [gitflow](http://nvie.com/posts/a-successful-git-branching-model/). 

## How to setup

### Generate a Github token

1. Go to settings
2. Personal access token
3. Click on generate new token
4. Type a Token Description ex: *glow CLI*
5. Check repo checkbox *(repo Full control of private repositories)*
6. Generate token

### Install the application

If you want to use it on the entire system, prefix this command with sudo

```
python setup.py install
pip3 install --force-reinstall .
pip3 install .
```

## Usage

To use this command, just type ```git glow``` in a git repository

### Feature

#### Start a feature

Development of new features starting from the **develop** branch.

```bash
git glow start feature 1234 simple description of my issue
```

#### Review a feature

To generate a Pull Request in order to merge your **feature** into **develop** branch.

```bash
git glow review feature 1234
```

### Release

#### Start a new release

To create a release from the last features merged on the **develop** branch.

```bash
git glow start release
```

#### Review a release

To generate a Pull Request in order to merge your **release** into **main** branch.

```bash
git glow review release
```

#### Finish a release

Close release branches and generate a tag for your release.
And merge the generated tag into **develop** branch.

```bash
git glow finish release
```


### Hotfix

#### Start a new hotfix

To create a hotfix from the last release merged on the **main** branch.

```bash
git glow start hotfix
```

#### Review a hotfix

To generate a Pull Request in order to merge your **hotfix** into **main** branch.

```bash
git glow review hotfix
```

#### Finish a hotfix

Close hotfix branches and generate a tag for your hotfix.
And merge the generated tag into **develop** branch.

```bash
git glow finish hotfix
```


## TODO

- [ ] Factorize `finish_release` and `finish_hotfix`
- [ ] Implement cancel methods:
    - [ ] `cancel_feature` 
    - [ ] `cancel_release` 
    - [ ] `cancel_feature` 
- [ ] Better handling for changelog generation and tag
- [ ] Improve slugify
- [ ] Secure creation
    - [ ] feature
    - [ ] release
    - [ ] hotfix


