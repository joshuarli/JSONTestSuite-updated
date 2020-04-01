#!/usr/bin/env python3

import io
import os
import os.path
import subprocess
import json
import shutil

from os import listdir
from time import strftime

BASE_DIR = os.path.dirname(os.path.realpath(__file__))
PARSERS_DIR = os.path.join(BASE_DIR, "parsers")
TEST_CASES_DIR_PATH = os.path.join(BASE_DIR, "test_parsing")
LOGS_DIR_PATH = os.path.join(BASE_DIR, "results")
LOG_FILENAME = "logs.txt"
LOG_FILE_PATH = os.path.join(LOGS_DIR_PATH, LOG_FILENAME)

INVALID_BINARY_FORMAT = 8

programs = {
    "python2.7.17": {
        "url": "",
        "cmdline": [
            "docker",
            "run",
            # not creating net namespaces shaves off ~0.5s
            "--net",
            "host",
        ],
    },
}


def run_tests(restrict_to_path=None, restrict_to_program=None):

    FNULL = open(os.devnull, "w")
    log_file = open(LOG_FILE_PATH, "w")

    prog_names = list(programs.keys())
    prog_names.sort()

    if isinstance(restrict_to_program, io.TextIOBase):
        restrict_to_program = json.load(restrict_to_program)

    if restrict_to_program:
        prog_names = filter(lambda x: x in restrict_to_program, prog_names)

    for prog_name in prog_names:
        d = programs[prog_name]

        url = d["url"]
        cmdline = d["cmdline"]

        if not shutil.which(cmdline[0]):
            print("-- skip non-existing", cmdline[0])
            continue

        for root, dirs, files in os.walk(TEST_CASES_DIR_PATH):
            json_files = (f for f in files if f.endswith(".json"))
            for filename in json_files:

                if restrict_to_path:
                    restrict_to_filename = os.path.basename(restrict_to_path)
                    if filename != restrict_to_filename:
                        continue

                file_path = os.path.join(root, filename)

                my_stdin = FNULL

                a = cmdline + [
                    "-v",
                    f"{file_path}:/tmp/test-payload.json",
                    f"jsontestsuite-{prog_name}",
                ]

                print("--", " ".join(a))

                try:
                    status = subprocess.call(
                        a,
                        stdin=my_stdin,
                        stdout=FNULL,
                        stderr=subprocess.STDOUT,
                        timeout=5,
                    )
                except subprocess.TimeoutExpired:
                    print("timeout expired")
                    s = "%s\tTIMEOUT\t%s" % (prog_name, filename)
                    log_file.write("%s\n" % s)
                    print("RESULT:", result)
                    continue
                except OSError as e:
                    if e.errno == INVALID_BINARY_FORMAT:
                        print("-- skip invalid-binary", commands[0])
                        continue
                    raise e

                result = None
                if status == 0:
                    result = "PASS"
                elif status == 1:
                    result = "FAIL"
                else:
                    result = "CRASH"

                s = None
                if result == "CRASH":
                    s = "%s\tCRASH\t%s" % (prog_name, filename)
                elif filename.startswith("y_") and result != "PASS":
                    s = "%s\tSHOULD_HAVE_PASSED\t%s" % (prog_name, filename)
                elif filename.startswith("n_") and result == "PASS":
                    s = "%s\tSHOULD_HAVE_FAILED\t%s" % (prog_name, filename)
                elif filename.startswith("i_") and result == "PASS":
                    s = "%s\tIMPLEMENTATION_PASS\t%s" % (prog_name, filename)
                elif filename.startswith("i_") and result != "PASS":
                    s = "%s\tIMPLEMENTATION_FAIL\t%s" % (prog_name, filename)

                # assert s is not None
                if s is None:
                    s = "%s\tEXPECTED_RESULT\t%s" % (prog_name, filename)

                print(s)
                log_file.write("%s\n" % s)

    FNULL.close()
    log_file.close()


def f_underline_non_printable_bytes(bytes):

    html = ""

    has_non_printable_characters = False

    for b in bytes:

        is_not_printable = b < 0x20 or b > 0x7E

        has_non_printable_characters |= is_not_printable

        if is_not_printable:
            html += "<U>%02X</U>" % b
        else:
            html += "%c" % b

    if has_non_printable_characters:
        try:
            html += " <=> %s" % bytes.decode("utf-8", errors="ignore")
        except:
            pass

    if len(bytes) > 36:
        return "%s(...)" % html[:36]

    return html


def f_status_for_lib_for_file(json_dir, results_dir):

    txt_filenames = [f for f in listdir(results_dir) if f.endswith(".txt")]

    # comment to ignore some tests
    statuses = [
        "EXPECTED_RESULT",
        "SHOULD_HAVE_FAILED",
        "SHOULD_HAVE_PASSED",
        "CRASH",
        "IMPLEMENTATION_FAIL",
        "IMPLEMENTATION_PASS",
        "TIMEOUT",
    ]

    d = {}
    libs = []

    for filename in txt_filenames:
        path = os.path.join(results_dir, filename)

        with open(path) as f:
            for l in f:
                comps = l.split("\t")
                if len(comps) != 3:
                    print("***", comps)
                    continue

                if comps[1] not in statuses:
                    print("-- unhandled status:", comps[1])

                (lib, status, json_filename) = (comps[0], comps[1], comps[2].rstrip())

                if lib not in libs:
                    libs.append(lib)

                json_path = os.path.join(TEST_CASES_DIR_PATH, json_filename)

                if json_path not in d:
                    d[json_path] = {}

                d[json_path][lib] = status

    return d, libs


def f_status_for_path_for_lib(json_dir, results_dir):

    txt_filenames = [f for f in listdir(results_dir) if f.endswith(".txt")]

    # comment to ignore some tests
    statuses = [
        "EXPECTED_RESULT",
        "SHOULD_HAVE_FAILED",
        "SHOULD_HAVE_PASSED",
        "CRASH",
        "IMPLEMENTATION_FAIL",
        "IMPLEMENTATION_PASS",
        "TIMEOUT",
    ]

    d = {}  # d['lib']['file'] = status

    for filename in txt_filenames:
        path = os.path.join(results_dir, filename)

        with open(path) as f:
            for l in f:
                comps = l.split("\t")
                if len(comps) != 3:
                    continue

                if comps[1] not in statuses:
                    # print "-- unhandled status:", comps[1]
                    continue

                (lib, status, json_filename) = (comps[0], comps[1], comps[2].rstrip())

                if lib not in d:
                    d[lib] = {}

                json_path = os.path.join(TEST_CASES_DIR_PATH, json_filename)

                d[lib][json_path] = status

    return d


def f_tests_with_same_results(libs, status_for_lib_for_file):

    tests_with_same_results = (
        {}
    )  # { {lib1:status, lib2:status, lib3:status} : { filenames } }

    files = list(status_for_lib_for_file.keys())
    files.sort()

    for f in files:
        prefix = os.path.basename(f)[:1]
        lib_status_for_file = []
        for l in libs:
            if l in status_for_lib_for_file[f]:
                status = status_for_lib_for_file[f][l]
                lib_status = "%s_%s" % (status, l)
                lib_status_for_file.append(lib_status)
        results = " || ".join(lib_status_for_file)
        if results not in tests_with_same_results:
            tests_with_same_results[results] = set()
        tests_with_same_results[results].add(f)

    r = []
    for k, v in tests_with_same_results.items():
        r.append((k, v))
    r.sort()

    return r


def generate_report(report_path, keep_only_first_result_in_set=False):

    (status_for_lib_for_file, libs) = f_status_for_lib_for_file(
        TEST_CASES_DIR_PATH, LOGS_DIR_PATH
    )

    status_for_path_for_lib = f_status_for_path_for_lib(
        TEST_CASES_DIR_PATH, LOGS_DIR_PATH
    )

    tests_with_same_results = f_tests_with_same_results(libs, status_for_lib_for_file)

    with open(report_path, "w", encoding="utf-8") as f:

        f.write(
            """<!DOCTYPE html>

        <HTML>

        <HEAD>
            <TITLE>JSON Parsing Tests</TITLE>
            <LINK rel="stylesheet" type="text/css" href="style.css">
            <META charset="UTF-8">
        </HEAD>

        <BODY>
        """
        )

        prog_names = list(programs.keys())
        prog_names.sort()

        libs = list(status_for_path_for_lib.keys())
        libs.sort()

        title = "JSON Parsing Tests"
        if keep_only_first_result_in_set:
            title += ", Pruned"
        else:
            title += ", Full"

        f.write("<H1>%s</H1>\n" % title)
        f.write(
            '<P>Appendix to: seriot.ch <A HREF="http://www.seriot.ch/parsing_json.php">Parsing JSON is a Minefield</A> http://www.seriot.ch/parsing_json.php</P>\n'
        )
        f.write("<PRE>%s</PRE>\n" % strftime("%Y-%m-%d %H:%M:%S"))

        f.write(
            """
        <A NAME="color_scheme"></A>
        <H4>Color scheme:</H4>
        <TABLE>
            <TR><TD class="EXPECTED_RESULT">expected result</TD><TR>
            <TR><TD class="SHOULD_HAVE_PASSED">parsing should have succeeded but failed</TD><TR>
            <TR><TD class="SHOULD_HAVE_FAILED">parsing should have failed but succeeded</TD><TR>
            <TR><TD class="IMPLEMENTATION_PASS">result undefined, parsing succeeded</TD><TR>
            <TR><TD class="IMPLEMENTATION_FAIL">result undefined, parsing failed</TD><TR>
            <TR><TD class="CRASH">parser crashed</TD><TR>
            <TR><TD class="TIMEOUT">timeout</TD><TR>
        </TABLE>
        """
        )

        ###

        f.write('<A NAME="all_results"></A>\n')
        f.write("<H4>Full Results</H4>\n")
        f.write("<TABLE>\n")

        f.write("    <TR>\n")
        f.write("        <TH></TH>\n")
        for lib in libs:
            f.write('        <TH class="vertical"><DIV>%s</DIV></TH>\n' % lib)
        f.write("        <TH></TH>\n")
        f.write("    </TR>\n")

        for (k, file_set) in tests_with_same_results:

            ordered_file_set = list(file_set)
            ordered_file_set.sort()

            if keep_only_first_result_in_set:
                ordered_file_set = [ordered_file_set[0]]

            for path in [path for path in ordered_file_set if os.path.exists(path)]:

                f.write("    <TR>\n")
                f.write("        <TD>%s</TD>" % os.path.basename(path))

                status_for_lib = status_for_lib_for_file[path]
                bytes = open(path, "rb").read()

                for lib in libs:
                    if lib in status_for_lib:
                        status = status_for_lib[lib]
                        f.write('        <TD class="%s">%s</TD>' % (status, ""))
                    else:
                        f.write('        <TD class="EXPECTED_RESULT"></TD>')
                f.write("        <TD>%s</TD>" % f_underline_non_printable_bytes(bytes))
                f.write("    </TR>")

        f.write("</TABLE>\n")

    if os.path.exists("/usr/bin/open"):
        os.system('/usr/bin/open "%s"' % report_path)


if __name__ == "__main__":
    restrict_to_path = None

    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("restrict_to_path", nargs="?", type=str, default=None)
    parser.add_argument(
        "--filter",
        dest="restrict_to_program",
        type=argparse.FileType("r"),
        default=None,
    )
    args = parser.parse_args()

    run_tests(args.restrict_to_path, args.restrict_to_program)

    generate_report(
        os.path.join(BASE_DIR, "results/parsing.html"),
        keep_only_first_result_in_set=False,
    )
