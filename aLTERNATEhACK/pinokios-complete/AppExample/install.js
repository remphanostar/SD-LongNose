module.exports = {
  run: [
    {
      when: "{{platform === 'win32'}}",
      method: "shell.run",
      params: {
        message: "set"
      }
    },
    {
      method: "shell.run",
      params: {
        message: [
          "git clone https://github.com/Tencent/Hunyuan3D-2 app"
        ]
      }
    },
    {
      method: "script.start",
      params: {
        uri: "torch.js",
        params: {
          venv: "env",                // Edit this to customize the venv folder path
          path: "app",                // Edit this to customize the path to start the shell from
          // xformers: true   // uncomment this line if your project requires xformers
        }
      }
    },
    {
      method: "shell.run",
      params: {
        venv: "env",                // Edit this to customize the venv folder path
        path: "app",                // Edit this to customize the path to start the shell from
        message: [
          "uv pip install -r requirements.txt"
        ]
      }
    },
    {
      when: "{{platform === 'linux'}}",
      method: "shell.run",
      params: {
        message: [
          "conda install -y -c conda-forge 'gxx<12'",
          "which g++"
        ]
      }
    },
    // Edit this step with your custom install commands
    {
      when: "{{platform === 'linux'}}",
      method: "shell.run",
      params: {
        build: true,
        venv: "../../../env",                // Edit this to customize the venv folder path
        env: {
          USE_NINJA: 0,
          DISTUTILS_USE_SDK: 1,
          NVCC_PREPEND_FLAGS: "-ccbin {{which('g++')}}"
        },
        path: "app/hy3dgen/texgen/custom_rasterizer",                // Edit this to customize the path to start the shell from
        message: [
          "python setup.py install"
        ]
      }
    },
    {
      when: "{{platform !== 'linux'}}",
      method: "shell.run",
      params: {
        build: true,
        venv: "../../../env",                // Edit this to customize the venv folder path
        env: {
          USE_NINJA: 0,
          DISTUTILS_USE_SDK: 1
        },
        path: "app/hy3dgen/texgen/custom_rasterizer",                // Edit this to customize the path to start the shell from
        message: [
          "python setup.py install"
        ]
      }
    },
    {
      when: "{{platform === 'linux'}}",
      method: "shell.run",
      params: {
        build: true,
        venv: "../../../env",                // Edit this to customize the venv folder path
        env: {
          USE_NINJA: 0,
          DISTUTILS_USE_SDK: 1,
          NVCC_PREPEND_FLAGS: "-ccbin {{which('g++')}}"
        },
        path: "app/hy3dgen/texgen/differentiable_renderer",                // Edit this to customize the path to start the shell from
        message: [
          "python setup.py install"
        ]
      }
    },
    {
      when: "{{platform !== 'linux'}}",
      method: "shell.run",
      params: {
        build: true,
        venv: "../../../env",                // Edit this to customize the venv folder path
        env: {
          USE_NINJA: 0,
          DISTUTILS_USE_SDK: 1
        },
        path: "app/hy3dgen/texgen/differentiable_renderer",                // Edit this to customize the path to start the shell from
        message: [
          "python setup.py install"
        ]
      }
    },
    //{
    //  method: "fs.link",
    //  params: {
    //    venv: "app/env"
    //  }
    //}
  ]
}
