{ pkgs ? import <nixpkgs> {} }:

pkgs.mkShell {
  name = "python-sockets-dev";

  buildInputs = [
    pkgs.python3
    pkgs.python3Packages.pip
    pkgs.python3Packages.virtualenv
    pkgs.gcc
  ];

  shellHook = ''
    echo "Python socket dev environment ready."
    echo "Use: python3 yourfile.py"
  '';
}

