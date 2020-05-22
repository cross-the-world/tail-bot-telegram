from TailBot import TailBot


def main():
    tailBot = TailBot()
    try:
        tailBot.activate_bot()
    finally:
        tailBot.stop_bot()
        print('Tail Bot terminated')

if __name__ == '__main__':
    main()