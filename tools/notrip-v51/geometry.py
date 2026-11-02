"""Build the v5.1 No-Trip Sleeve as sold and save the triangles for the renderers.

The geometry comes from the v5.1 CAD source in the NoTrip OneDrive folder (the same
code that writes the print files), so every picture is of the current part:

    standard   one 6 in body, a connector locking each end (windows at 12 and 36 mm)
    large      two 6 in bodies butted end to end, a connector bridging the joint and
               one locking each far end (three) - the two-pack as sold

Each assembly is saved twice, with the dog's name on the connector and with a blank
top, because the name is optional. Body and connector triangles stay separate so a
render can tell them apart.

    set NOTRIP_V51_SRC=...\\v5.1 connector - Oct 29 2026\\src   (default below)
    py -3 tools/notrip-v51/geometry.py            -> tools/notrip-v51/build/*.npz
"""
import os
import pathlib
import sys

import numpy as np

HERE = pathlib.Path(__file__).resolve().parent
BUILD = HERE / 'build'
SRC = pathlib.Path(os.environ.get('NOTRIP_V51_SRC', pathlib.Path.home() / 'OneDrive' / 'Attachments' / 'Documents'
                   / '1. Kinor Partners' / 'Clients & Products' / '8. NoTrip Sleeve' / '3D-print'
                   / 'v5.2 connector on end - Nov 1 2026' / 'src'))   # v5.2 = v5.1 body + connector shape
sys.path.insert(0, str(SRC))

import notrip_v5 as N  # noqa: E402
import connector as K  # noqa: E402

NAME = 'BUDDY'   # the example name in every picture (Oz's test print)


def tris(man):
    m = man.to_mesh()
    return np.array(m.vert_properties)[:, :3][np.array(m.tri_verts)].astype(np.float32)


def main():
    BUILD.mkdir(exist_ok=True)
    L, c = K.C['seg_len'], K.C['pitch_c']
    seg, _, _ = N.build_body(L, K.body_windows(L), 'full')
    for tag, name in (('name', NAME), ('blank', '')):
        K.C['name'] = name
        con, _, _ = K.build_connector('R')
        # The connector is built centred on z=0 over a joint; 2c in from an end it locks that
        # end. As sold (owner, 2026-10-30) every sleeve comes with two clips: Standard has one
        # at each end, Large has one at each far end and one bridging the join - three in all.
        std = dict(body=tris(seg), clip=np.concatenate([tris(con.translate((0, 0, 2 * c))),
                                                        tris(con.translate((0, 0, L - 2 * c)))]))
        large = dict(body=np.concatenate([tris(seg.translate((0, 0, -L))), tris(seg)]),
                     clip=np.concatenate([tris(con.translate((0, 0, -L + 2 * c))), tris(con),
                                          tris(con.translate((0, 0, L - 2 * c)))]))
        np.savez_compressed(BUILD / f'standard-{tag}.npz', **std)
        np.savez_compressed(BUILD / f'large-{tag}.npz', **large)
        np.savez_compressed(BUILD / f'clip-{tag}.npz', clip=tris(con))
        print(tag, 'body', len(std['body']), 'clip', len(std['clip']), 'tris')


if __name__ == '__main__':
    main()
