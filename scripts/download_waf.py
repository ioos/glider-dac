#!/usr/bin/env python
'''
scripts/download_waf.py

A script to scrape ISO 19115 Documents from a running ERDDAP instance. In the
case of Glider DAC, this should download from the public ERDDAP isntance. The
documents should be in a directory with no other contents and served as a
static directory.
'''

import requests
import argparse
import os
import sys

from thredds_crawler.crawl import Crawl

def main(args):
    if args.erddap:
        get_erddap_waf(args.erddap, args.destination)
    if args.thredds:
        get_thredds_waf(args.thredds, args.destination)

def get_thredds_waf(url, destination_path):
    '''
    Scrapes the available ISO files at the specified THREDDS instance.
    The URL must point to the catalog.xml
    '''
    c = Crawl(url)
    datasets = c.datasets
    for dataset in datasets:
        services = { row['name'] : row for row in dataset.services }
        iso_url = services['iso']['url']
        if iso_url:
            file_path = get_iso_doc(iso_url, destination_path, dataset.id + '.xml')
            print "Created ISO at", file_path

def get_erddap_waf(url, destination_path):
    '''
    Scrapes the available datasets from ERDDAP and harvests the ISO 19115
    documents that are available. This script currently does not gather
    metadata on the 'all' aggregate datasets that ERDDAP provides.
    '''
    url = url.rstrip('/')
    index_url = url + '/info/index.json'
    response = requests.get(index_url)
    if response.status_code != 200:
        raise IOError("Failed to get index from ERDDAP at %s" % index_url)
    doc = response.json()
    datasets = create_dataset_doc(doc)
    check_destination(destination_path)

    for dataset_id in datasets:
        if dataset_id.startswith('all'):
            continue

        iso_url = datasets[dataset_id]['ISO 19115']
        if iso_url:
            file_path = get_iso_doc(iso_url, destination_path)
            print "Created ISO at", file_path

def check_destination(destination_path):
    '''
    Creates the directory if it doesn't exist
    '''
    if not os.path.exists(destination_path):
        os.makedirs(destination_path)

def create_dataset_doc(doc):
    '''
    Creates a python dictionary of the ERDDAP index JSON response

    { 
        dataset_id : {
            col_name : row value
        }
    }
    '''
    columns = { col_name : i for i,col_name in enumerate(doc['table']['columnNames']) }
    datasets = {}
    for row in doc['table']['rows']:
        dataset_id = row[ columns['Dataset ID'] ]
        datasets[dataset_id] = { col_name : row[ columns[col_name] ] for col_name in columns }

    return datasets

def get_iso_doc(iso_url, destination_path, file_name=None):
    '''
    Downloads an ISO document at the URL specified into the destination
    '''
    response = requests.get(iso_url, stream=True)
    if response.status_code != 200:
        raise IOError("Failed to retrieve ISO 19115 Document from ERDDAP at %s with error code %s" % (iso_url, response.status_code) )

    xml_doc = response.text
    file_name = file_name or iso_url.split('/')[-1]

    file_path = os.path.join(destination_path, file_name)
    with open(file_path, 'wb') as f:
        for chunk in response.iter_content(chunk_size=4096):
            if chunk:
                f.write(chunk)
                f.flush()

    return file_path


if __name__ == '__main__':

    parser = argparse.ArgumentParser(description='Download ISO documents from ERDDAP instance')
    parser.add_argument('destination', help='Folder to download the ISO documents into')
    parser.add_argument('-e', '--erddap', help='URL to ERDDAP, example: http://coastwatch.pfeg.noaa.gov/erddap')
    parser.add_argument('-t', '--thredds', help='URL to THREDDS catalog.xml, example: http://data.ioos.us/gliders/thredds/catalog.xml')
    args = parser.parse_args()

    main(args)



