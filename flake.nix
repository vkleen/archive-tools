{
  inputs = {
    nixpkgs = {
      url = github:NixOS/nixpkgs;
    };
    poetry2nix = {
      url = github:nix-community/poetry2nix;
      inputs.nixpkgs.follows = "nixpkgs";
      inputs.flake-utils.follows = "flake-utils";
    };
    flake-utils = {
      url = github:numtide/flake-utils;
    };

    dymopipe = {
      url = github:vkleen/dymopipe;
    };
  };

  outputs = { self, nixpkgs, ... }@inputs: {
    overlay = nixpkgs.lib.composeManyExtensions [
      inputs.poetry2nix.overlay
    ];
  } // (inputs.flake-utils.lib.eachDefaultSystem (system:
    let
      pkgs = import "${inputs.nixpkgs}/pkgs/top-level" {
        localSystem = { inherit system; };
        overlays = [ self.overlay ];
      };

      poetryOverrides = pkgs.poetry2nix.overrides.withDefaults (final: prev: {
        pyzbar = prev.pyzbar.overridePythonAttrs (_: {
          postPatch = ''
            substituteInPlace pyzbar/zbar_library.py \
              --replace \
                "find_library('zbar')" \
                '"${pkgs.lib.getLib pkgs.zbar}/lib/libzbar${pkgs.stdenv.hostPlatform.extensions.sharedLibrary}"'
          '';
        });
        pydyf = prev.pydyf.overridePythonAttrs (o: {
          nativeBuildInputs = (o.nativeBuildInputs or [ ]) ++ [ final.flit-core ];
        });
        weasyprint = prev.weasyprint.overridePythonAttrs (o: {
          patches = pkgs.lib.head o.patches;
        });
      });

      extraBuildInputs = [ ];

      poetryArgs = {
        projectDir = ./.;
        overrides = poetryOverrides;
      };

      archive = pkgs.poetry2nix.mkPoetryApplication
        (poetryArgs // {
          propagatedBuildInputs = extraBuildInputs;
          preFixup = ''
            for p in $out/bin/*; do
              wrapProgram "$p" --suffix-each PATH : "${inputs.dymopipe.defaultPackage.${system}}/bin:${pkgs.imagemagick}/bin:${pkgs.ghostscript}/bin"
            done
          '';
        });
      poetryShell = pkgs.poetry2nix.mkPoetryEnv poetryArgs;
    in
    {
      packages = rec {
        inherit archive;
        default = archive;
      };

      devShell = pkgs.mkShell {
        inputsFrom = [ poetryShell.env ];
        buildInputs = [
          pkgs.pyright
          pkgs.poetry
        ] ++ extraBuildInputs;
      };
    }
  ));
}
