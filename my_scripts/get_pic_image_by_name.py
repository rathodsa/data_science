def get_pic_image_by_name(client=None, display_name=None):
    if client and display_name:
        pic_records = []
        found_images = OrderedDict()

        image_name_re = "^{}".format(display_name)

        # Load the PIC app listing info
        try:
            resp = oci.pagination.list_call_get_all_results(client.list_app_catalog_listings,
                                                            publisher_type="ORACLE", sort_order="DESC")

        except oci.exceptions.ServiceError as e:
            raise SystemExit("ERROR: Looking for images with display-name matching {} failed. "
                             "OCI Msg: {}".format(image_name_re, e.message))
        else:
            test_re = re.compile(image_name_re)
            for listing_data in resp.data:
                if test_re.search(listing_data.display_name):
                    pic_records.append(listing_data)

        for pr in pic_records:
            try:
                # This is sorted by time released so we only care about the first/latest one
                # https://docs.cloud.oracle.com/iaas/api/#/en/marketplace/20181001/ListingSummary/ListListings
                resp = oci.pagination.list_call_get_all_results(client.list_app_catalog_listing_resource_versions,
                                                                sort_order="DESC",
                                                                listing_id=pr.listing_id)
            except oci.exceptions.ServiceError as e:
                logger.error("ERROR: Unable to determine image id for PIC Image {}"
                             "OCI Msg: {}".format(image_name_re, e.message))
                raise SystemExit(e)
            else:
                image_id = resp.data[0].listing_resource_id

            try:
                resp = client.get_image(image_id)
            except oci.exceptions.ServiceError as e:
                logger.error("Unable to get image for OCID: {}"
                             "OCI Msg: {}".format(image_id, e.message))
                raise SystemExit(e)
            else:
                image = resp.data
                found_images[image.display_name] = image

    return found_images
