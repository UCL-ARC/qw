# Proposed Quality Workflow (QW) user guide - release 1

The Quality Workflow tool (QW) aims to help reduce the friction in creating and maintaining traceability matrices
(later release could target hazards and risks).

# Background and use-case

Within medical device software there are several design and development stages that should be tracked,
versioned and a traceability matrix is a standard way of presenting this information.
The Quality Management System used in WEISS is document based, which requires substantial manual effort in tracking linkages,
updating of versions and ensuring that all approvals are current.

The QW allows users to track the different changes in design and development requirements, outputs, verification and validations.
These different stages are linked together using github or gitlab as part of the normal development process.
QW also will ensure that versioning of items are updated if their contents have changed,
and notify when manual verification should be rerun due to changes in requirements or outputs.

# Actual and Potential Features

- [x] Manage project on hosted service
  - [x] github.com
  - [ ] gitlab anywhere
- [x] Issues as regulated objects
  - [x] User Needs
  - [x] Requirements
  - [ ] Hazardous Situation
  - [ ] Risk Mitigation
  - [ ] Anomaly (bug) template
    - [ ] Risk analysis in comment
- [x] Pull Requests as regulated objects
  - [x] Design Objects
  - [x] Automated workflow
    - [x] Cannot merge without review
    - [x] Cannot merge without traceability to User Needs
    - [x] User configurability of checks
- [ ] Automated test gathering?
  - [ ] Ensure automated tests pass before PR merge?
- [ ] Extra information (in CSV files?)
  - [ ] Manual test script description
  - [ ] Manual test run results
  - [ ] Risk class of each component
  - [ ] Risk likelihood, impact, matrix
  - [ ] Decision for each risk not entered as a Hazardous Situation issue
- [x] Produce documents from data in repo and service
  - [x] MS Word document
  - [ ] Markdown document production
  - [ ] Excel document production
  - [x] "database file" production to allow users to make their own document templates with MS word or LibreOffice
  - [ ] Built-in standards documents
    - [ ] ISO13485
    - [ ] DCB0129
  - [x] Inserting data into documents
    - [x] Data produces repeated, nested paragraphs
    - [ ] Data produces repeated rows in tables
    - [ ] Data produces charts
  - [ ] Management documentation
    - [ ] Burndown charts
      - [ ] Or burnup charts
      - [ ] Requirements satisfied with Design Object (PR)
      - [ ] User Needs covered with Requirements
      - [ ] User Needs satisfied with Design Objects
      - [ ] Anomalies remaining in different risk categories
    - [ ] Remaining items report
      - [ ] Anomalies
      - [ ] Requirements
      - [ ] User Needs
      - [ ] Risk decisions made/yet to be made
      - [ ] Unmet risks

# Setup

## Installation

### Using pipx

Install the latest version from github:

```
pipx install git+https://github.com/UCL-ARC/qw
```

Install a particular version from github:

```
pipx install git+https://github.com/UCL-ARC/qw@v1.0
```

Install from the source code directory:

```
pipx install .
```

### Using conda

After creating and activating your conda environment (with
`conda create` and `conda activate`), install `qw` into
that environment with:

```
conda install pip git
pip install git+https://github.com/UCL-ARC/qw
```

### Using venv

The `qw` tool requires python 3.9 or greater, if your project is in python then we suggest adding it to the developer requirements.
If not, you may want to create a virtual environment for your python, one option is the [venv](https://docs.python.org/3.9/library/venv.html) module.

For Unix:

```shell
python -m venv venv --prompt qw # create virtual environment directory called `venv`
source venv/bin/activate  # use the virtual environment
pip install git+https://github.com/UCL-ARC/qw.git#egg=qw  # install qw
echo "venv" >> .gitignore. # ensure git ignores the `venv` directory
```

## Configuration using Github

### Initial setup and adding to repository

The `qw` tool creates a `.qw` directory that allows versions of each design and development stage to be tracked at release time.
Add this directory to your version control, so that there is a shared baseline at each release.
In the first step it also creates a set of GitHub actions and templates to ensure the tool can work correctly.
To allow the `qw` to interact with GitHub you will need to create a fine-grained personal access token.
The final step of configuration then updates your GitHub repository with rules, and add templates for each stage of the quality workflow (and another
template if there is an issue or pull request that doesn't relate to the quality management documentation).

#### Initialise `qw`

At the top level of your git repository, run the intialisation step for github

```shell
qw init --repo github.com:username/reponame --service github
```

> INFO: A ".qw" directory has been created
>
> INFO: Github actions for qw have been added to your ".github" directory
>
> INFO: Please commit the files after you have finished your setup
>
> INFO: Rulesets and branch protection added for branches matching "main" to "stefpiatek/dummy-medical-software"

If you have a different development flow than pull requests into main/master then edit the `qw` ruleset for the repository,
adding extra branches to the ruleset (e.g. `develop`)

<!--
- [name=Stef] or do we just define what workflow they have to use? Could also give a comma separated list of branch names in the --git-service option?
-->

You can omit `--service github` if the repo is at `github.com` (as in
this case) and you can omit `--repo <url>` if you have the desired
repository configured as the git remote named `upstream` (or `origin`
if you have no `upstream` remote set).

#### Setup Personal Access Token

- Follow
  the [GitHub instructions](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/managing-your-personal-access-tokens#creating-a-fine-grained-personal-access-token)
  we suggest the following configuration options:

  | field             | value, user defined values defined by `${...}`              |
  | ----------------- | ----------------------------------------------------------- |
  | Token name        | `qw-${repository_name}`                                     |
  | Expiration        | `custom...` then choose 364 days from today                 |
  | Description       | `QW tool for ${repository_name}`                            |
  | Repository access | `Only select repositories` -> Select the project repository |
  | Permissions       | Only add repository permissions, see next table             |

  | repository permissions | value          |
  | ---------------------- | -------------- |
  | Actions                | Read and write |
  | Administration         | Read and write |
  | Contents               | Read-only      |
  | Issues                 | Read and write |
  | Metadata               | Read-only      |
  | Pull Requests          | Read and write |

  Then click the `Generate token` button and copy the token (you can't get its value again if you close the page).

- Add the personal access token to your machine's keychain (uses [keyring](https://pypi.org/project/keyring/))

  ```shell
  qw login
  ```

  <!--
     - [name=Stef] For this I guess we should implement it in keyring using: service=`qw:github.com` username=`owner/repo`?
     - [name=Stef] Should try and get a windows user early on to test that keyring works as expected
  -->

  > Please copy the personal access token and hit enter:

  After you've done this, the system will check the personal access token. If you've configured for the remote
  URL <https://github.com/stefpiatek/dummy-medical-software> you would see:

  > INFO there are currently 27 issues and PRs
  >
  > Can connect to remote repository :tada:

### Setup for a new user, on an existing project that uses QW

The local and GitHub repository have already been configured to work with `qw`, you'll just need
to [add the personal access token](#setup-personal-access-token)

### Customising configuration for identifiers

QW initialises with a `System` component for requirements (used for generating a unique identifier, short code value is `X`).
You can add extra components to the configuration by editing the `/.qw/components.csv`

```
name,short-code,description
System,X,Whole system requirements.
Drug dosage,D,Drug dosage calculation module.
```

You set up the workflow files and the release templates files like this:

```shell
qw configure --workflow
qw configure --release-templates basic
```

At the moment `basic` is the only option for release templates at the moment.
In the future we should have options such as `iso13485`, `dbc0129` and
`management` to allow you to produce regulatory documents and management
documents without having to build them yourself.

### Customization of checks

By default, `qw check` and the checks installed for gating PRs will fail if any check fails.
This can be customized by editing `.qw\conf.json`. Look for the `"checks"` property,
which looks something like this:

```json
{
  "checks": {
    "User need links have qw-user-need label": "error",
    "User Need links must exist": "error",
    "Closing Issues are Requirements": "error"
  }
}
```

You can turn behaviours off by changing `"error"` to `"off"`, or keep the
check reporting but not preventing PRs from merging by changing `"error"`
to `"warning"`:

```json
{
  "checks": {
    "User need links have qw-user-need label": "warning",
    "User Need links must exist": "error",
    "Closing Issues are Requirements": "off"
  }
}
```

If this change appears as part of a PR, the change will affect the workflow
action gating this PR. For example, if your PR is failing checks, you can
simply turn them off to get your PR through! It is currently up to the
reviewer to make sure that this is not being abused!

## Configuration using Gitlab

Gitlab is not supported yet. When it is, it will work both on gitlab.com and on
instances hosted elsewhere.

# Using QW with github

QW uses existing issues and pull requests to track the different design and development stages along with managing risks and their mitigations.

## Creating QW items

### User needs

- In your github repository, Add a new issue, selecting the User needs template
  ![](https://hackmd.io/_uploads/Syo1w1oy6.png)
- Fill out the required fields and any other information if it exists
  ![](https://hackmd.io/_uploads/rJG7_1okT.png)
- Hit `Submit new issue` and the issue will be rendered like this: ![](https://hackmd.io/_uploads/BktGcJo1p.png)
- The first comment of this issue will be used by `qw` for tracking, but you can edit anything manually after the `Other information` header and this
  will not interfere with the tool

### Requirements

- In your github repository, Add a new issue, selecting the User needs template
  ![](https://hackmd.io/_uploads/Syo1w1oy6.png)
- Fill out the required fields and any other information that may be useful
  ![](https://hackmd.io/_uploads/B1X07JVZ6.png)
  - The options for requirements type are:
    - Functional
    - System inputs and outputs
    - Application programming interface
    - Alarms and warnings
    - Security
    - User interface
    - Data definition and database
    - Installation and acceptance
    - Operation methods and maintenance
    - Networking
    - User maintenance
    - Regulatory
- Hit `Submit new issue` and theissue will be rendered like this:
  ![](https://hackmd.io/_uploads/Bycax6yfp.png)
  - Note that the `design-component-d` has been added as "Drug dosage" was added as a component type with a short code of `D`.
- The first comment of this issue will be used by `qw` for tracking, but you can edit anything manually after the `Other information` header and this
  will not interfere with the tool
- The parent issue will have been updated with this issue number
  ![](https://hackmd.io/_uploads/S1OvqDrW6.png)

### Design outputs and design verification

- Create a pull request from github and follow the instructions on the template
  ![](https://hackmd.io/_uploads/BkYpd7ikp.png)
  - If the `qw-ignore` tag is added, then this PR does is not related to the medical device aspect of the software
- In this example, the pull request contains the design outputs and design verification. These can be added separately, where the design verification
  would also be linked to the requirement.
  ![](https://hackmd.io/_uploads/ryp39Xj1a.png)
- QW will check that the chain of design items are able to be processed and fully signed off,
  when this is successful the github action will pass
  ![](https://hackmd.io/_uploads/H1Ix67i16.png)
- QW requires a pull request that is labelled as a `design-validation` or `design-verification` to have at least one automated test that targets a
  specific `design-output`, `requirement` or `user-need`
  - Tests are tracked manually in `.qw/test_mapping.csv` where multiple issues are separated by `;`, in the following structure
    test name | issue(s) targeted
    -- | --
    InputVerifierTests::testWeightIsNegative | 40
    InputVerifierTests::testConversionOfWeightUnits | 4;23
    acceptance_test_user_entry.docx | 2
  - The development team may want to write a script that allows them to get the names of all tests run and ensure that automated tests listed in the
    csv still exist, bonus points if you make this an automated test that fails if a test doesn't exist
  - Adding the manual verification test scripts to version control is ideal, but you may also list the name
  - the QW CI task will fail if:
    - No parent issue is given for a PR
    - A test doesn't exist which is mapped to the parent issue
    - The structure of the `test_mapping.csv` has been altered, or `;` has not been used to separate targeted issues
    - A test name is duplicated in `test_mapping.csv`

### Design validation

- QW does not require design validation documentation to be added to the repository,
  but you may add the test script.
  Ideally this would be in a plain text format. We suggest creating a
  `validation` directory and storing the validation information there
- As with [Design outputs and design verification](#design-outputs-and-design-verification), update the `.qw/test_mapping.csv` with the test script(s)
  that fulfill the user need.
- Create a pull request from github and follow the instructions on the template
  ![](https://hackmd.io/_uploads/BkYpd7ikp.png)
  - A validation links to a user need, so link this type of issue in the PR
  - Assign the pull request to the team member who will authorise the validation.
    Once they have validated it and signed any required paperwork,
    they should approve the PR.

### Non-QW items

- If you'd like to create an issue that doesn't relate to the medical device then use the `Non QW item` issue template.
  This tags the issue with `qw-ignore` so that QW does not parse the issue.
  ![](https://hackmd.io/_uploads/SkWcEzQgp.png)
- If you'd like to create a pull request that doesn't relate to the medical device then tag the pull request with `qw-ignore`.

## Closing QW items when they are not resolved by a PR

**Note**: this functionality has not yet been completed.

- There may be times when a QW-tracked issue is required to be closed not by a PR.
- You may close the issue as either `completed` or `not planned` ![](https://hackmd.io/_uploads/Sy22Bi9x6.png)
- Then please add another section to QW information in the issue in the form:

  ```markdown
  ### Closure reason

  #### type

  <!-- allowed types: duplicate, cannot replicate, not a defect, won't fix -->

  duplicate

  #### explanation

  Duplicate of #5
  ```

## Checking QW items for consistency

You can check that all the closing issues of all PRs (not marked with
`qw-ignore`) are requirements, that all Requirements have User Needs
links and that all these User Needs links are marked with `qw-user-need`:

```sh
qw check --remote
```

There are clearly many more checks that we could run in this stage.

The `--remote` flag tells `qw` to examine the PRs and issues as they
currently exist on the server. The alternative is:

```sh
qw check --local
```

This checks the PRs and issues as they were gathered by the last
invocation of the `qw freeze` command, described next.

## Versioning of QW items

The `qw freeze` function is used to save the current state of the qw items in github, and to ensure that the versions of items are updated if their
information has changed.
This should be run regularly, which will update or add to the `.qw` directory.
These changes should be committed and added to the main development branch by a pull request as a [Non QW item](#non-qw-items).

```shell
qw freeze
```

An example incrementing a tag upon update:

> Running WQ freeze
> Found 47 QW items
>
> INFO: Requirement https://github.com/stefpiatek/dummy-medical-software/issues/6 has been updated since last saved
>
> Previous data:
>
> - Description : Warfarin dosage should be calculated using based on patient age, gender and weight
> - Parent User need: https://github.com/stefpiatek/dummy-medical-software/issues/5
>
> Current Data:
>
> - Description : Warfarin dosage in mg/kg should be calculated using based on patient age, gender and weight
> - Parent User need: https://github.com/stefpiatek/dummy-medical-software/issues/5
>
> Would you like to increment the version? (y/n): <prompt response from user - y>
>
> INFO: Updated tag to "qw-v2"
>
> INFO: There are 2 design outputs that link to this Requirement, please ensure one of them has the "qw-v2" tag if it resolves the updated
> information
>
> - https://github.com/stefpiatek/dummy-medical-software/pull/7
> - https://github.com/stefpiatek/dummy-medical-software/pull/12
>
> ...
>
> INFO: :heavy_check_mark: 12 new QW items added to state
>
> INFO: :heavy_check_mark: 47 QW items checked
>
> INFO: Please commit the changes in the ".qw" directory

Example response when the change is trivial and does not warrant a change in the version of the QW item:

> ...
>
> Would you like to increment the version? (y/n): <prompt response from user - n>
>
> INFO: Tag kept at "qw-v1", data for the Requirement has been updated to the current state
>
> ...

### Creating a documentation release

When you're ready to update the documentation in your Quality Management System (QMS), you can use the QW tool's `release` command.
Running this will create word documents based on the QW template for export

```shell
qw release
```

This turns the files in the `qw_release_templates` directory into the same
named files (within the same named subdirectories) into correctly filled-in
documents in the `qw_release_out` directory. Any paragraphs containing
mailmerge fields will be repeated however many times they need to be to
be filled in with all the data qw knows about. Also, dependent paragraphs
below those repeated paragraphs (at "higher" outline level) will be repeated.
The mailmerge fields in these dependent paragraphs will be filled with
dependent data from qw.

If you want to write your own document template, or update them, you
need to be able to add these mailmerge fields to your document. For this
you need a "database file". Get that from the `qw generate-merge-fields`
command. This produces a file called `fields.csv`.

What do we do with this `fields.csv` file? In MS Word you choose
"Select Recipients|Use Existing List..." from the "Mailings" ribbon, then
select the `fields.csv` file. Now the "Insert Merge Field" button lets you
add fields. In LibreOffice you select "Insert|Field|More Fields...". In the
dialog that pops up, select the "Database" tab, highlight the "Mail Merge
Fields" type. In the "Add database file" box click the "Browse..." button
and select the `fields.csv` file. Now the fields appear in the right hand
box. You can select the one you want and click "Insert". You can keep
the dialog open as you type if you like.

Now, as long as you save this new file within the `qw_release_templates`
directory, `qw release` will fill in your document and output the result to the
`qw_release_out` directory.

You probably want to add `qw_release_out` to your `.gitignore` file,
especially if you are adding the documents inside it to some other QMS tool.

## Tab completion of commands

You can use tab to complete the subcommands of `qw`, for example you can type
`qw gen` then press tab, and `qw generate-merge-fields` will appear, but only
if you have installed the tab completions. Do this with the following on Windows:

```sh
qw --install-completion powershell
```

to get tab completion in PowerShell. Similarly on Linux, Mac or WSL use:

```sh
qw --install-completion bash
```

or use the `zsh` or `fish` options if you use those shells.

# FAQ and common issues

- Can I import an existing project into QW
  - There's nothing stopping this, though each issue and pull request would need to match the required format, and be tagged appropriately by the
    time you'd like to run a release. This may be a reasonable amount of work and we expect issues may need to be created.
