#!/usr/bin/env python
from os.path import join
import argparse

from glob import glob
import pandas as pd

if __name__ == "__main__":
    arg = argparse.ArgumentParser(
        description="merge individual transit predictions output by mirai"
    )
    arg.add_argument(
        "input_dir", help="directory location", type=str, default="."
    )
    arg.add_argument(
        "-s",
        "--save",
        help="save merged file",
        action="store_true",
        default=False,
    )
    arg.add_argument(
        "-ext", help="file extension to read (default='csv')", default="csv"
    )
    args = arg.parse_args()
    indir = args.input_dir
    ext = args.ext

    filelist = glob(join(indir, f"*.{ext}"))
    assert len(filelist) > 0, f"no {ext} file found"

    ds = []
    for i in filelist:
        d = pd.read_csv(i)
        name = i.split(indir)[1].split("/")[1].split("_")[0]
        if "name" not in d.columns:
            d.insert(0, "name", name)
        ds.append(d)

    df = pd.concat(ds)
    df = df.drop("Unnamed: 0", axis=1)
    if args.save:
        fp = join(indir, "merged.csv")
        df.to_csv(fp, index=False)
        print(f"Saved: {fp}")
    else:
        print(df)
