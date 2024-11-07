class CompanyService:
    def __init__(self, client, logger):
        self.client = client
        self.logger = logger
    
    def get_company(self, public_id):
        """Fetch data about a given LinkedIn company.

        https://www.diffchecker.com/uYLloHfx/

        :param public_id: LinkedIn public ID for a company
        :type public_id: str

        :return: Company data
        :rtype: dict
        """
        query_id = "voyagerOrganizationDashCompanies.54122aa9bd2308dc9bf3bc525e2efb2e"
        variables = {
            "universalName": public_id,
        }

        res = self.client.get_graphql(
            query_id=query_id,
            variables=variables,
            # headers={"accept": "application/vnd.linkedin.normalized+json+2.1"},
        )
        data = res.json()
        import ipdb

        ipdb.set_trace()
        if data and "status" in data and data["status"] != 200:
            self.logger.error(
                "request failed: {}".format(
                    data["message"] if "message" in data else "<no message given>"
                )
            )
            return {}

        # $type = "com.linkedin.restli.common.CollectionResponse"
        # recipeTypes = ["com.linkedin.0f028a70ae137e00e6802cde39614073"]
        # company_urn = data["data"]["data"]["organizationDashCompaniesByUniversalName"][
        #     "*elements"
        # ][0]
        # response_type = "com.linkedin.voyager.dash.organization.Company"
        # company = [
        #     i
        #     for i in data["included"]
        #     if i["$type"] == response_type and i["entityUrn"] == company_urn
        # ][0]

        company = data["data"].get("organizationDashCompaniesByUniversalName", {}).get("elements", [])[0]

        print(company.keys())

        return company
