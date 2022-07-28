Git Glow
########


A simple git extension to use `git flow branching model <http://nvie.com/posts/a-successful-git-branching-model/>`_ automatically with Github and `semver <https://semver.org/>`_ to tags your releases and hotfixes.

Requirements
************

- git
- Python 3.7+
- Jira project already setup

How to setup
============

Installation
------------

.. code-block:: bash

    pip install git-glow


Configuration
-------------

Configuration begins during the first command.

For example, just request to start a new feature (according you already have a Jira project, with a "GLOW" key and a "GLOW-1234" ticket, otherwize a 404 error will be prompted at the end of this operation):

.. code-block:: bash

    git glow start feature 1234

Following messages will be prompted, waiting an answer for each step::

    Create a glow config? [Y/n] y
    Jira Project Key? GLOW
    Github Repository Name? [:owner/:name] nicolasramy/git-glow
    Github Token? ghp_XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
    Start feature name: «feature/GLOW-1234» [y/n] y

- Jira Project Key is a key that you chosed when you created your Jira project and you can retrieve as prefix of your Jira tickets (like GLOW-1234)
- Github Repository Name is same as described in the prompted message: ``the_repository_owner/the_project_name``
- Github token is an access token you can set from your GitHub settings: https://github.com/settings/tokens.
  This token will require "Full control of private repositories" (``repo`` checkbox when you create it).
  After being created, you just need to copy-paste the generated token.

If the configuration successfully registered and you think it was wrong, you can update it in the ``.git/config`` of your project. The following section should exist::

      github-token = ghp_XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
      github-repository-name = nicolasramy/git-glow
      jira-project-key = GLOW

Usage
=====

To use this command, just type git glow in a git repository
with a **develop** and **master** branch.

Feature
-------

.. code-block:: bash

    git glow start feature 1234
    git glow review feature 1234
    git glow finish feature 1234

Release
-------

.. code-block:: bash

    git glow start release
    git glow review release
    git glow finish release

Hotfix
------

.. code-block:: bash

    git glow start hotfix
    git glow review hotfix
    git glow finish hotfix
