from wml.repl import start_repl, execute_file


def main() -> None:
    print("World Modeling Language (WML)")
    # start_repl()
    execute_file(filename="examples/program.wml")


if __name__ == "__main__":
    main()
