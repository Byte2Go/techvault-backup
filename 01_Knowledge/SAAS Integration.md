Technical Assessment: Purpose is to evaluate SaaS Cloud Integration with DG System and identify any constraints and risk associated with such integration.
	 **SaaS Integration** with DG Azure AD for Authentication, SaaS will require access to DG MS Graph API (However sharing Gaph API is not recommended).-> A temporary admin account will be created for DG Azure Admin to grant Graph API pwermission to the SaaS System during registration. This temporary account will be deleted after registration acticvity is completed, which will take approx 30 minutes. 

**Tennent Restriction:**  How DG Azure Conditional Access policy need to be updated to allow login trafffic from tatent address.  A conditional access policy needs to be enforced at the DG end for SaaS app targeting the Tenant Source. This policy will validate user's AD group membership and Source IP. 

User will login SaaS App using DG Microseft Login App.