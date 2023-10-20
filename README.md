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

# Setup

## Installation

The `qw` tool requires python 3.9 or greater, if your project is in python then we suggest adding it to the developer requirements.
If not, you may want to create a virtual environment for your python, one option is the [venv](https://docs.python.org/3.9/library/venv.html) module.

For Unix:

```shell
python -m venv env --prompt qw # create virtual environment directory called `venv`
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
> INFO: Github actions for qw have been added to your ".github" directory
> INFO: Templates added to your ".github" directory: "User need", "Requirement", "Design output", "Pull request"
> INFO: Please commit the files after you have finished your setup
> INFO: Rulesets and branch protection added for branches matching "main" to "stefpiatek/dummy-medical-software"

If you have a different development flow than pull requests into main/master then edit the `qw` ruleset for the repository,
adding extra branches to the ruleset (e.g. `develop`)

<!--
- [name=Stef] or do we just define what workflow they have to use? Could also give a comma separated list of branch names in the --git-service option?
-->

You can omit `--service github` if the repo is at `github.com` (as in
this case) and you can omit `--repo <url>` if you have the desired
repository configured as the git remote named `upstream`.

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

  > INFO: Can access "stefpiatek/dummy-medical-software"

### Setup for a new user, on an existing project that uses QW

The local and GitHub repository have already been configured to work with `qw`, you'll just need
to [add the personal access token](#setup-personal-access-token)

### Customising configuration for identifiers

QW creates identifiers for User Needs and Requirements.

| Design stage | format                                              | example      |
| ------------ | --------------------------------------------------- | ------------ |
| User Need    | `URS-U${user need number}`                          | URS-U001     |
| Requirement  | `REQ-${component short code}-${requirement number}` | REQ-SWR-0001 |

QW initialises with a `System` component for requirements (used for generating a unique identifier, short code value is `X`).
You can add extra components to the configuration by editing the `/.qw/components.csv`

```
name,short-code,description
System,X,Whole system requirements.
Drug dosage,D,Drug dosage calculation module.
```

```shell
qw config --update
```

> INFO: Added "Drug dosage (D)" to local components, ensure that the updated file is committed.
> INFO: Added tag "qw-component-d" to GitHub

## Configuration using Gitlab

Intentionally left blank at the moment for brevity. Will aim for being able to implement this.

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
> INFO: Updated tag to "qw-v2"
> INFO: There are 2 design outputs that link to this Requirement, please ensure one of them has the "qw-v2" tag if it resolves the updated
> information
>
> - https://github.com/stefpiatek/dummy-medical-software/pull/7
> - https://github.com/stefpiatek/dummy-medical-software/pull/12
>   ...
>   INFO: :heavy_check_mark: 12 new QW items added to state
>   INFO: :heavy_check_mark: 47 QW items checked
>   INFO: Please commit the changes in the ".qw" directory

Example response when the change is trivial and does not warrant a change in the version of the QW item:

> ...
> Would you like to increment the version? (y/n): <prompt response from user - n>
> INFO: Tag kept at "qw-v1", data for the Requirement has been updated to the current state
> ...

### Creating a documentation release

When you're ready to update the documentation in your Quality Management System (QMS), you can use the QW tool's `release` command.
Running this will:

- Ensure that all issues and pull requests have been marked with `qw-ignore` or one of the `qw-` item tags, raising an error (and stopping) to ensure
  all items are tagged
- Ensure that all QW items have versions
- Ensure the entire chain `design validation -> design verification -> design output -> requirement -> user need` is consistent with QW rules,
  starting from the furthest stage of QW items. So if there is no `design validation`, then the chain will start from `design verification`. If there
  was only a `user need` and `requirement`s, then only these would be validated
- Create word documents based on the QW template for export
- [name=Stef] Optionally? Create an html page that shows a burndown graph for each of the QW item types, showing the number completed and outstanding
  over time. Would this be useful?

```shell
qw release qms_docs
```

> Creating a release for QW
> Creating "qms_docs" directory if it doesn't already exist, and overwriting any previously exported files
> INFO: :heavy_check_mark: 47 QW items checked
> INFO: :heavy_check_mark: Documents have been written to the "qms_docs" directory

# FAQ and common issues

- Can I import an existing project into QW
  - There's nothing stopping this, though each issue and pull request would need to match the required format, and be tagged appropriately by the
    time you'd like to run a release. This may be a reasonable amount of work and we expect issues may need to be created.
-

# Open questions

- Which document parts are the most useful for export, and would we want the user to be able to edit the template (update styles and placeholder
  text?)
- Would the burndown chart be useful to get an overview for development?
- Gate who can authorise a PR, or can anyone?
- Should we include a change request at this stage, or keep it with the risk management side of things
- closed not by a PR - would be useful to get a steer on what is required or most useful
