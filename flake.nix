{
  description = "fika - open source DIY cappuccino machine (ESP32 + ESPHome + copper, brass and aluminum)";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixpkgs-unstable";
    # Shared ESPHome tooling (validation gate, QEMU simulator). Carries its
    # own nix-qemu-espressif input for the .#sim shell. Update with:
    # nix flake update esphome-skills
    esphome-skills.url = "github:heavy-oil1462/esphome-skills";
  };

  outputs = { self, nixpkgs, esphome-skills }:
    let
      systems = [ "x86_64-linux" "aarch64-linux" "x86_64-darwin" "aarch64-darwin" ];
      forAllSystems = f: nixpkgs.lib.genAttrs systems (system:
        f system nixpkgs.legacyPackages.${system});
    in
    {
      # default: everything for the validation gate and simulator UI.
      # sim: + Espressif QEMU for tools/test_sim.py. No docker compose:
      # fika has no server stack.
      devShells = forAllSystems (system: pkgs:
        esphome-skills.lib.mkShells {
          inherit pkgs system;
          withCompose = false;
          shellHook = ''
            echo "fika devshell - see tools/, scripts/ and .claude/skills/"
            echo "  python3 scripts/regen_all.py    # rebuild all derived artifacts"
            echo "  scripts/verify_design.sh        # read-only verify gate"
            echo "  python3 tools/validate.py       # software validation gate"
            echo "  nix develop .#sim               # + QEMU for tools/test_sim.py"
          '';
        });
    };
}
