The core difference is that ==**a code push uploads your local changes to a remote server**, while **a Pull Request (PR) is a formal request to review and merge those uploaded changes into a main project branch**==. <mark style="background: #D2B3FFA6;">You must perform a code push _before_ you can open a PR. </mark>

### Quick Comparison

| Feature        | Code Push (`git push`)                      | Pull Request (PR)                                               |
| -------------- | ------------------------------------------- | --------------------------------------------------------------- |
| **What it is** | A Git command line action.                  | A web platform feature ([GitHub](https://github.com/), GitLab). |
| **Purpose**    | Transfer data from local PC to remote repo. | Collaborative code review and integration.                      |
| **Visibility** | Updates the designated online branch.       | Creates an open discussion thread for a team.                   |
| **Automation** | Saves your code backup in the cloud.        | Triggers automated testing (CI/CD pipelines).                   |

---

### Code Push (`git push`)
A code push is a technical mechanism using Git software.
- It is like <mark style="background: #ABF7F7A6;">saving a local document directly up to a cloud folder.</mark>
- It <mark style="background: #ADCCFFA6;">executes immediately via your terminal interface</mark> <mark style="background: #BBFABBA6;">without needing permissions from others.</mark>
- Teams usually use a <mark style="background: #D2B3FFA6;">code push to update their individual feature branches.</mark>
- Pushing directly to a primary branch (`main` or `master`) is <mark style="background: #FFB8EBA6;">risky because it skips peer review and can break production software. </mark>

### Pull Request (PR)
A PR is a collaborative process hosted on git platforms like [GitHub Pull Requests](https://docs.github.com/pull-requests/collaborating-with-pull-requests/proposing-changes-to-your-work-with-pull-requests/about-pull-requests) or [Azure Repos](https://learn.microsoft.com/en-us/azure/devops/repos/git/about-pull-requests?view=azure-devops). 
- It acts like a "suggested edit" workflow where <mark style="background: #FFB86CA6;">peers look over modifications before they go live.</mark>
- It displays line-by-line differences between your new branch and the target branch.
- It enables <mark style="background: #ADCCFFA6;">team members to spot bugs, discuss architectural logic, and leave feedback.</mark>
- Once reviews pass and automated checks succeed, <mark style="background: #D2B3FFA6;">the PR is merged into the main codebase. </mark>

### **The Standard Workflow**
In modern team development, these two concepts work together sequentially: 
1. Create a local feature branch on your computer.
2. Write code and <mark style="background: #ADCCFFA6;">commit those changes locally.</mark>
3. <mark style="background: #D2B3FFA6;">Run a **code push** to send that branch up to the remote server.</mark>
4. <mark style="background: #BBFABBA6;">Open a **Pull Request (PR)** on the server to merge your feature branch into `main`</mark>