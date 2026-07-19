{
  description = "fika - open source DIY cappuccino machine (ESP32 + ESPHome + copper, brass and aluminum)";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixpkgs-unstable";
    # Espressif's QEMU fork (esp32 machine + open_eth NIC) for the simulator
    # (docs/SIMULATION.md, tools/test_sim.py). Deliberately NOT following our
    # nixpkgs: keeping upstream's lock means the substituted/cached build is
    # reused instead of compiling QEMU from source.
    nix-qemu-espressif.url = "github:SFrijters/nix-qemu-espressif";
  };

  outputs = { self, nixpkgs, nix-qemu-espressif }:
    let
      systems = [ "x86_64-linux" "aarch64-linux" "x86_64-darwin" "aarch64-darwin" ];
      forAllSystems = f: nixpkgs.lib.genAttrs systems (system:
        f system nixpkgs.legacyPackages.${system});
    in
    {
      devShells = forAllSystems (system: pkgs:
        let
          basePackages = with pkgs; [
            # firmware
            esphome
            # linting / validation
            yamllint
            # local broker + clients for the simulator and debugging
            mosquitto
            # tools/*.py + sim/*.py
            (python3.withPackages (ps: with ps; [ paho-mqtt ]))
            jq
          ];
        in
        {
          default = pkgs.mkShell {
            packages = basePackages;
            shellHook = ''
              echo "fika devshell - see tools/, scripts/ and .claude/skills/"
              echo "  python3 scripts/regen_all.py    # rebuild all derived artifacts"
              echo "  scripts/verify_design.sh        # read-only verify gate"
              echo "  python3 tools/validate.py       # software validation gate"
              echo "  nix develop .#sim               # + QEMU for tools/test_sim.py"
            '';
          };
          # Everything above + Espressif QEMU for the real-firmware simulator
          # (tools/test_sim.py, docs/SIMULATION.md). Separate shell: QEMU may
          # build from source (~20 min) and most contributors never need it.
          sim = pkgs.mkShell {
            packages = basePackages
              ++ [ nix-qemu-espressif.packages.${system}.qemu-esp32 ];
          };
        });
    };
}
