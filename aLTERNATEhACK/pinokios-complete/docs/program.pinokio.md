As you requested, here is the comprehensive markdown file created from the Pinokio website.

# Pinokio Documentation

## Introduction

Pinokio is a browser that lets you locally install, run, and automate any AI on your computer. Everything you can run in your command line can be automated with Pinokio script, with a user-friendly UI.

You can use Pinokio to automate anything, including:

*   Install AI apps and models
*   Manage and Run AI apps
*   Create workflows to orchestrate installed AI apps
*   Run any command to automate things on your machine and more...

### Community Help

*   **X (Twitter):** Follow @cocktailpeanut on X to stay updated on all the new scripts being released and feature updates.
*   **Discord:** Join the Pinokio discord to ask questions and get help.

## Install

### Windows

**Step 1. Download**

Download for Windows

**Step 2. Unzip**

Unzip the downloaded file and you will see a .exe installer file.

**Step 3. Install**

Run the installer file. You may see a Windows warning. To bypass this, click "More Info" then "Run anyway".

### Mac

**Step 1. Download**

*   Download for Apple Silicon Mac (M1/M2/M3/M4)
*   Download for Intel Mac

**Step 2. Install (IMPORTANT!!)**

The Pinokio Mac installer ships with Sentinel built in. Sentinel lets you run open source apps that are NOT on the Apple App store. You just need to drag and drop the installed Pinokio.app onto Sentinel to "Remove app from Quarantine".

### Linux

For linux, you can download and install directly from the latest release on Github.

## Programming Pinokio

### Components

A Pinokio launcher is made up of 4 types of files:

*   **Config:** `pinokio.json` determines how the project is displayed. (auto-generated)
*   **Environment:** `ENVIRONMENT` stores environment variables to be auto-imported into all scripts in the project. (auto-generated)
*   **Script:** The actual script files that can run stuff.
*   **Launcher:** `pinokio.js` builds the UI that displays links to the scripts.

### Config (`pinokio.json`)

This file stores project information like title, icon, and description.

**Syntax:**

```json
{
  "title": "<title>",
  "description": "<description>",
  "icon": "<icon>",
  "posts": [ "<x.com url>", ... ],
  "links": [
    { "title": "<title>", "value": "<value>" },
    { "title": "<title>", "links": [ ... ] }
  ]
}
```

### Environment (`ENVIRONMENT`)

This file stores custom environment variables that get imported into scripts automatically. The format is the standard unix shell variable format.

### Script

Scripts are written in JSON or JavaScript and contain the logic to be executed.

**Syntax:**

```json
{
  "version": "<schema_version>",
  "run": [ <step>, ... ],
  "daemon": <daemon>,
  "env": [ <prerequisite_env>, ... ]
}
```

*   **`version`**: Script schema version (current is 4.0).
*   **`run`**: An array of steps to be executed sequentially.
*   **`daemon`**: If `true`, the script keeps running after all steps are finished.
*   **`env`**: An array of required environment variables.

### Launcher (`pinokio.js`)

This file creates a menu UI for launching scripts.

**Syntax:**

```javascript
module.exports = {
  "version": "<script_schema_version>",
  "pre": [<pre>],
  "menu": [<menu>],
}
```

*   **`version`**: The schema version (latest is "4.0").
*   **`pre`**: An array of prerequisites.
*   **`menu`**: An array of tab items, or an async function that returns the menu items.

## API

Pinokio provides a rich API for interacting with the system.

### `shell`

#### `shell.run`

Starts an instant shell, runs commands, and closes the shell.

**Syntax:**

```json
{
  "method": "shell.run",
  "params": {
    "input": <boolean>,
    "message": <string|array>,
    "path": "<path>",
    "env": { ... },
    "venv": "<venv_path>",
    "conda": "<conda_config>",
    "on": [ ... ],
    "sudo": <boolean>,
    "cache": "<cache_path>"
  }
}
```

### `input`

Accepts user input through a modal dialog.

**Syntax:**

```json
{
  "method": "input",
  "params": {
    "title": "<title>",
    "description": "<description>",
    "form": [
      {
        "type": "<input_type>",
        "key": "<key>",
        "title": "<title>",
        ...
      }
    ]
  }
}
```

### `filepicker`

Opens a file or folder picker dialog.

**Syntax:**

```json
{
  "method": "filepicker.open",
  "params": {
    "title": "<dialog_title>",
    "type": "<folder|file>",
    ...
  }
}
```

### `fs` (File System)

Provides functions for file system operations.

*   `fs.write`: Writes data to a file.
*   `fs.read`: Reads data from a file.
*   `fs.rm`: Deletes a file or folder.
*   `fs.copy`: Copies a file or folder.
*   `fs.download`: Downloads a file.
*   `fs.link`: Creates virtual drives.
*   `fs.open`: Opens a file or folder in the file explorer.
*   `fs.cat`: Prints the contents of a file to the terminal.

### `jump`

Jumps to a specific step in the `run` array.

**Syntax:**

```json
{
  "method": "jump",
  "params": {
    "<index|id>": "<value>",
    "params": { ... }
  }
}
```

### `local`

#### `local.set`

Sets local variables for the current script execution.

**Syntax:**

```json
{
  "method": "local.set",
  "params": {
    "<key>": "<value>",
    ...
  }
}
```

### `json`

Provides functions for working with JSON files.

*   `json.set`: Sets a value in a JSON file.
*   `json.rm`: Removes attributes from a JSON file.
*   `json.get`: Assigns JSON file contents to local variables.

### `log`

Prints messages to the terminal.

**Syntax:**

```json
{
  "method": "log",
  "params": {
    "<type>": "<data>"
  }
}
```

### `net`

Makes network requests.

**Syntax:**

```json
{
  "method": "net",
  "params": {
    "url": "<url>",
    "method": "<get|post|delete|put>",
    "headers": { ... },
    "data": { ... }
  }
}```

### `notify`

Displays a push notification.

**Syntax:**

```json
{
  "method": "notify",
  "params": {
    "html": "<html>",
    "href": "<href>",
    "target": "<target>"
  }
}
```

### `script`

Provides functions for managing scripts.

*   `script.download`: Downloads a script from a git URI.
*   `script.start`: Starts a script.
*   `script.stop`: Stops a running script.
*   `script.return`: Returns a value from a script.

### `web`

#### `web.open`

Opens a URL in a browser.

**Syntax:**

```json
{
  "method": "web.open",
  "params": {
    "uri": "<uri>",
    ...
  }
}
```

### `hf`

An API for accessing the Hugging Face CLI.

#### `hf.download`

Downloads files from Hugging Face.

**Syntax:**

```json
{
  "method": "hf.download",
  "params": {
    ...
  }
}
```

## Memory

Pinokio provides a set of memory variables that can be used in scripts.

*   **`input`**: The value passed from the previous step.
*   **`args`**: The parameters passed to the script when it was launched.
*   **`local`**: Local variables for the current script execution.
*   **`self`**: The script object itself.
*   **`uri`**: The URI of the current script.
*   **`port`**: The next available port.
*   **`cwd`**: The current working directory.
*   **`platform`**: The operating system (`darwin`, `linux`, `win32`).
*   **`arch`**: The system architecture.
*   **`gpus`**: An array of available GPUs.
*   **`gpu`**: The first available GPU.
*   **`current`**: The index of the current step.
*   **`next`**: The index of the next step.
*   **`envs`**: Environment variables.
*   **`which`**: Checks if a command exists.
*   **`kernel`**: The kernel JavaScript API.
*   **`_`**: The lodash utility library.
*   **`os`**: The Node.js `os` module.
*   **`path`**: The Node.js `path` module.

## File System

Pinokio uses a self-contained file system to isolate apps and their dependencies. All files are stored in the Pinokio home folder, which can be configured in the settings.

The main folders are:

*   **`api`**: Stores downloaded apps.
*   **`bin`**: Stores globally installed modules.
*   **`cache`**: Stores cached files.
*   **`drive`**: Stores virtual drives.
*   **`logs`**: Stores log files.

## Tutorials

The Pinokio documentation provides a number of tutorials to get you started, including:

*   Hello world
*   Run multiple commands
*   Install packages into venv
*   Run an app in venv
*   Download a file
*   Call a script from another script
*   Install, start, and stop remote scripts
*   Build UI with pinokio.js
*   Publish your script
*   Install script from any git url
*   List your script on the directory
*   Auto-generate app launchers 
Of course. Here is the continuation of the comprehensive markdown file for the Pinokio documentation.

## Tutorials (Continued)

### Hello world

This tutorial demonstrates how to create a simple "Hello, world!" script.

**`hello.json`**
```json
{
  "run": [{
    "method": "shell.run",
    "params": {
      "message": "echo 'hello world'"
    }
  }]
}
```

To run this, you can drag and drop the `hello.json` file onto the Pinokio browser.

### Run multiple commands

You can run multiple commands sequentially in a single `shell.run` step.

```json
{
  "run": [{
    "method": "shell.run",
    "params": {
      "message": [
        "echo 'hello'",
        "echo 'world'"
      ]
    }
  }]
}
```

### Install packages into venv

This example shows how to create a virtual environment and install packages into it.

```json
{
  "run": [{
    "method": "shell.run",
    "params": {
      "message": "python -m venv env"
    }
  }, {
    "method": "shell.run",
    "params": {
      "venv": "env",
      "message": "pip install gradio"
    }
  }]
}
```

### Run an app in venv

This script launches a Python web app using the virtual environment created previously.

```json
{
  "run": [{
    "method": "fs.write",
    "params": {
      "path": "app.py",
      "text": "import gradio as gr\ndemo = gr.Blocks()\nwith demo:\n    gr.Markdown(\"start typing to see the output\")\n    with gr.Row():\n        inp = gr.Textbox(placeholder=\"what is your name?\")\n        out = gr.Textbox()\n    inp.change(lambda x: f\"welcome {x}!\", inp, out)\ndemo.launch()"
    }
  }, {
    "method": "shell.run",
    "params": {
      "venv": "env",
      "message": "python app.py",
      "on": [{
        "event": "/http://\\S+/",
        "done": true
      }]
    }
  }]
}
```

### Build UI with pinokio.js

The `pinokio.js` file allows you to create a user interface for your project.

**`pinokio.js`**
```javascript
module.exports = {
  menu: [{
    html: "Run",
    href: "run.json"
  }, {
    html: "Install",
    href: "install.json"
  }]
}
```

### Publish your script

You can publish your scripts to any public git repository (like GitHub or Hugging Face) and they can be run directly within Pinokio.

### Install script from any git url

To install a script from a git URL, you can use the `script.download` method:

```json
{
  "run": [{
    "method": "script.download",
    "params": {
      "uri": "https://github.com/pinokio-project/hello-world"
    }
  }]
}
```

## Advanced Topics

### Error Handling

You can handle errors within your scripts by using conditional logic with the `fs.exists` or other methods to check for expected outcomes, and then using the `jump` method to direct the script flow accordingly.

### Script Templates

Pinokio supports script templates which can be used as a starting point for creating new applications. These templates provide a basic structure and can be customized to fit specific needs.

### Custom Kernels

For advanced users, Pinokio allows the creation and use of custom kernels. This enables developers to extend the core functionality of Pinokio and integrate it with other systems.

## Conclusion

This document provides a comprehensive overview of the Pinokio platform, its features, and how to use them. For more in-depth information and the latest updates, please refer to the official Pinokio website and community channels.