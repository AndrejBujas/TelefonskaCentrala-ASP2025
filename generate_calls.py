import random
import time

FILE_LENGTH = 1000000


def str_time_prop(start, end, time_format, prop):
    """Get a time at a proportion of a range of two formatted times.

    start and end should be strings specifying times formatted in the
    given format (strftime-style), giving an interval [start, end].
    prop specifies how a proportion of the interval to be taken after
    start.  The returned time will be in the specified format.
    """

    stime = time.mktime(time.strptime(start, time_format))
    etime = time.mktime(time.strptime(end, time_format))

    ptime = stime + prop * (etime - stime)

    return time.strftime(time_format, time.localtime(ptime))


def random_date(start, end, prop):
    return str_time_prop(start, end, '%d.%m.%Y %H:%M:%S', prop)


def random_duration(min, max):
    duration = random.random()
    minutes = random.randrange(0, 60)
    seconds = random.randrange(0, 60)

    hours = 0

    if duration >= 0.9:
        hours = random.randrange(min, max)

    return "%02d:%02d:%02d" % (hours, minutes, seconds)


def generate_calls():
    with open("phones.txt") as input_file:
        with open("calls.txt", "w") as output_file:
            content = input_file.readlines()
            for current_index in range(FILE_LENGTH):
                date = random_date("01.01.2025 0:0:0",
                                   "18.09.2025 23:59:59",
                                   random.random())

                duration = random_duration(0, 10)
                while True:
                    caller_index = random.randrange(0, len(content))
                    callee_index = random.randrange(0, len(content))
                    if caller_index != callee_index:
                        break

                caller_number = content[caller_index].replace("\n", "").split(",")[1]
                callee_number = content[callee_index].replace("\n", "").split(",")[1]

                data = [caller_number, callee_number, date, duration]
                output_file.write(", ".join(data) + "\n")
                print("%d/%d" % (current_index, FILE_LENGTH))


def generate_blocks():
    number_of_blocked = 100
    choosen = set()

    with open("phones.txt") as input_file:
        with open("blocked.txt", "w") as output_file:
            content = input_file.readlines()
            while number_of_blocked > 0:
                index = random.randint(0, len(content))
                if index in choosen:
                    continue

                choosen.add(index)
                number = content[index].split(",")[1]
                output_file.write(number)
                number_of_blocked -= 1


if __name__ == '__main__':
    generate_calls()
    generate_blocks()


