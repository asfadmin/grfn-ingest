# About

The Getting Ready for NISAR (GRFN) project was designed to experiment with the functional architecture of Amazon Web Services cloud computing environment for the processing, distribution and archival of Synthetic Aperture Radar data in preparation for the [NASA-ISRO SAR Mission (NISAR)](https://nisar.jpl.nasa.gov/). The grfn-ingest pipeline is designed to manage large volumes of data at high rates (up to 50 Gbps), to simulate the data volumes anticipated for transfer and archival during the NISAR mission.

This repository contains the code developed and used by the [Alaska Satellite Facility (ASF)](https://www.asf.alaska.edu) to accept ingest data processed by the [Jet Propulsion Laboratory (JPL)](https://www.jpl.gov) from the [European Space Agency's (ESA)](www.esa.int/) [Sentinel-1a/1b](www.esa.int/Our_Activities/Observing_the_Earth/Copernicus/Sentinel-1) mission into representative level 2 interferogram data products. These representative products are then used by ASF to simulate [Distributed Active Archive Center (DAAC)](https://earthdata.nasa.gov/about/daacs) operations, including ingesting, archive, repackaging, cataloging, and distributing the
data.

# Copyright Notice + License:

*Copyright 2017 University of Alaska Fairbanks*

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

The Software is provided "as is," without warranty of any kind, express or implied, including but not limited to the warranties of merchantability, fitness for a particular purpose, and noninfringement. In no event shall the authors or copyright holders be liable for any claim, damages, or other liability, whether in an action of contract, tort, or otherwise, arising from, out of, or in connection with the software or the use or other dealings in the software.

# Architecture

![Architecture Diagram](/doc/architecture.png)

# Components

* **invoke:** A scheduled Lambda function that starts step function executions for each received message in the SQS job queue.
* **step-function:** A step function defining the workflow to ingest a single GRFN product.
* **verify:** A Lambda function that validates the received message as well as the files and metadata in the source S3 bucket.
* **ingest:** An EC2/ECS batch application that downloads product files, creates product zip files, and uploads final product artifacts to the output S3 buckets.
* **echo10-construction:** A Lambda function that generates an ECHO 10 XML metadata file for a particular product.
* **echo10-to-cmr:** A scheduled Lambda function that submits ECHO 10 XML metadata files to CMR.
* **notify:** A Lambda function that sends ingest success/failure messages to the SNS response topic.
* **metrics:** A scheduled Lambda function that populates a custom CloudWatch metric with the number of running step function executions.  Used to drive autoscaling for the ingest component.

# Build and Deployment Instructions

1. Run steps in buildspec.yaml
2. Deploy cloudformation-final.yaml

# Top Level Inputs and Outputs

## Runtime Inputs

Runtime inputs consist of the following staged files:

* metadata json file conforming to verify/src/metadata_schema.json browse image
* arbitrary product files (under a common s3 bucket and prefix)
  Send a message formatted per verify/src/message_schema.json to JobTopic

## Outputs

### Three product files:
* PrivateBucket/\<product-name\>.zip
* PrivateBucket/\<product-name\>.unw_geo.zip
* PrivateBucket/\<product-name\>.full_res.zip

### Browse file:
* PublicBucket/\<browse-file-name\>

### Product metadata reported to CmrGranuleUrl with these Collection Ids and Granule URs:
* Sentinel-1 All Interferometric Products (BETA) \<product-name\>-All
* Sentinel-1 Unwrapped Interferogram and Coherence Map (BETA) \<product-name\>-Unwrapped
* Sentinel-1 Full Resolution Wrapped Interferogram and DEM (BETA) \<product-name\>-Full
* Success/failure message conforming to ?? sent to DefaultResponseTopicArn

# Credits

## ASF

GRFN-ingest was written by the Alaska Satellite Facility.  The Alaska Satellite Facility downlinks, processes, archives, and distributes remote-sensing data to scientific users around the world. ASF's mission is to make remote-sensing data accessible.

### GRFN Team at ASF

The GRFN team at ASF that directly contributed to this project consists of:

  * Jessica Garron, Product Owner
  * Andrew Johnston, Scrum Master and developer
  * Ian Dixon, developer
  * David Matz, developer
  * John Mitchell, former GRFN developer

## NASA

ASF gratefully acknowledges the sponsorship of the National Aeronautics and Space Administration for this work.
