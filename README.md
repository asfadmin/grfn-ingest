# About

The Getting Ready for NISAR (GRFN) project was designed to experiment with the functional architecture of Amazon Web Services cloud computing environment for the processing, distribution and archival of Synthetic Aperture Radar data in preparation for the [NASA-ISRO SAR Mission (NISAR)](https://nisar.jpl.nasa.gov/). The grfn-ingest pipeline is designed to manage large volumes of data at high rates (up to 50 Gbps), to simulate the data volumes anticipated for transfer and archival during the NISAR mission.

This repository contains the code developed and used by the [Alaska Satellite Facility (ASF)](https://www.asf.alaska.edu) to accept ingest data processed by the [Jet Propulsion Laboratory (JPL)](https://www.jpl.gov) from the [European Space Agency's (ESA)](www.esa.int/) [Sentinel-1](www.esa.int/Our_Activities/Observing_the_Earth/Copernicus/Sentinel-1) mission into representative Level 2 interferogram data products. These representative products are then used by ASF to simulate [Distributed Active Archive Center (DAAC)](https://earthdata.nasa.gov/about/daacs) operations, including ingesting, archiving, repackaging, cataloging, and distributing the
data.

# Architecture

![Architecture Diagram](/doc/architecture.png)

# Components

* **invoke:** A scheduled Lambda function that starts step function executions for each received message in the SQS job queue.
* **step-function:** A step function defining the workflow to ingest a single GRFN data product.
* **verify:** A Lambda function that validates the received message as well as the files and metadata in the source S3 bucket.
* **ingest:** A Lambda function that copies product files from the source S3 bucket to the output S3 buckets.
* **echo10-construction:** A Lambda function that generates an ECHO 10 XML metadata file for a particular product.
* **cmr-token** A Lambda function that generates an access token for the CMR ingest API.
* **echo10-to-cmr:** A scheduled Lambda function that submits ECHO 10 XML metadata files to CMR.
* **notify:** A Lambda function that sends ingest success/failure messages to the SNS response topic.

# Build and Deployment Instructions

1. Run steps in buildspec.yaml
2. Deploy cloudformation-final.yaml

# Top Level Inputs and Outputs

## Runtime Inputs

Runtime inputs consist of the following staged files:

* metadata json file conforming to verify/src/metadata_schema.json
* browse image
* data product file
* Send a message formatted per verify/src/message_schema.json to JobTopic

## Outputs

### Product files:
* PrivateBucket/\<data-product-file-name\>

### Browse file:
* PublicBucket/\<browse-file-name\>

### Product metadata reported to CmrGranuleUrl with these Collection Ids and Granule URs:
* Sentinel-1 All Interferometric Products (BETA) \<product-name\>-All
* Success/failure message sent to DefaultResponseTopicArn

# Credits

## ASF

GRFN-ingest was written by the Alaska Satellite Facility.  The Alaska Satellite Facility downlinks, processes, archives, and distributes remote-sensing data to scientific users around the world. ASF's mission is to make remote-sensing data accessible.

## NASA

ASF gratefully acknowledges the sponsorship of the National Aeronautics and Space Administration for this work.
