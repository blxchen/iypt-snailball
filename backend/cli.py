"""Headless simulation and CSV analysis. python3 -m backend.cli --help"""
import argparse
import csv
import json
import pathlib
from .model import simulate
from .measurements import analyze

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    sub=parser.add_subparsers(dest='command',required=True)
    sim=sub.add_parser('simulate',help='Run the reduced model and write JSON.')
    sim.add_argument('--parameters',help='Path to a JSON object of model parameters.')
    sim.add_argument('--timestamps',help='Comma-separated sample times in seconds.')
    sim.add_argument('--output',required=True,help='Output JSON path.')
    measurement=sub.add_parser('analyze',help='Analyze a measured CSV with headers t,x and optional v.')
    measurement.add_argument('csv',help='Input CSV path.')
    measurement.add_argument('--unit',choices=['m','cm','mm'],default='m')
    measurement.add_argument('--fps',type=float,default=30)
    measurement.add_argument('--sigma-x',type=float,default=0,help='Position uncertainty in the selected distance unit.')
    measurement.add_argument('--sigma-t',type=float,default=0,help='Time uncertainty in seconds.')
    measurement.add_argument('--time-origin',default='0')
    measurement.add_argument('--position-origin',type=float,default=0)
    measurement.add_argument('--radius-mm',type=float,default=35)
    measurement.add_argument('--output',required=True,help='Output JSON path.')
    args=parser.parse_args()
    try:
        if args.command=='simulate':
            params=json.loads(pathlib.Path(args.parameters).read_text()) if args.parameters else None
            times=[float(v) for v in args.timestamps.split(',')] if args.timestamps else None
            result=simulate(params,times)
        else:
            with open(args.csv,encoding='utf-8-sig',newline='') as source:
                rows=list(csv.DictReader(line for line in source if line.strip() and not line.lstrip().startswith('#')))
            for row in rows:
                if row.get('v','').strip()=='':
                    row.pop('v',None)
            result=analyze(dict(rows=rows,distance_unit=args.unit,fps=args.fps,sigma_x=args.sigma_x,
                                sigma_t=args.sigma_t,time_offset=args.time_origin,
                                position_offset=args.position_origin,radius_mm=args.radius_mm))
        pathlib.Path(args.output).write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')
        print(f'Written {args.output}')
    except (ValueError,OSError,TypeError) as error:
        parser.exit(2,f'Error: {error}\n')

if __name__=='__main__':
    main()
