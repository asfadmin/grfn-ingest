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
* **metadata-construction:** A Lambda function that generates a CMR-compliant metadata file for a particular product.
* **cmr-token** A Lambda function that generates an access token for the CMR ingest API.
* **metadata-to-cmr:** A scheduled Lambda function that submits metadata files to CMR.
* **notify:** A Lambda function that sends ingest success/failure messages to the SNS response topic.

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

# Integration testing

From the repository root, run:

```bash
aws --profile grfn sns publish --topic-arn "arn:aws:sns:us-east-1:406893895021:ingest-test-jobs" --message file://tests/example-message.json
```

Wait a few minutes for the job to process (you can monitor it in the `ingest-test-jobs` Step Function).

There should be five CMR products published with each job:
the base NetCDF file, plus four GeoTIFFs: amplitude, coherence, unwrapped phase, and connected components.

Review the published products in CMR UAT using the following link:
<https://cmr.uat.earthdata.nasa.gov/search/granules.echo10?provider=ASF&producer_granule_id=S1-GUNW-A-R-014-tops-20230116_20220214-153036-00038E_00022N-PP-3708-v2_0_6>

You can also replace `.echo10` with `.json` or `.umm_json`.

Re-running a new job with the same `ProductName` field will overwrite the existing records in CMR.
Re-running the exact same job should only change the `InsertTime` and `LastUpdate` fields.

# Credits

## ASF

GRFN-ingest was written by the Alaska Satellite Facility.  The Alaska Satellite Facility downlinks, processes, archives, and distributes remote-sensing data to scientific users around the world. ASF's mission is to make remote-sensing data accessible.

## NASA

ASF gratefully acknowledges the sponsorship of the National Aeronautics and Space Administration for this work.
