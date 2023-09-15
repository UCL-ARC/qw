# prototype-ci-reading
Quick prototype for processing PR and issue data in github actions 

## Ensuring that we can access these parts in CI

Issues

- [x] Title
- [x] First comment
- [x] PR number
- [x] Assignee(s)
  - If we're using names, they're not required on github so could end up being blank
  - We could just use github logins and have part of the config that you have to map gh logins 
    to names as you want them on the report information
- [x] Label

PRs

- [x] Title
- [x] First comment
- [x] Assignee(s)
- [ ] Users who's final reviews were APPROVED
- [x] Label
- [x] [Linked Issues](https://github.com/cli/cli/discussions/7097#discussioncomment-5229031) 

