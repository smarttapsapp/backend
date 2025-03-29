UNSUPPORTEDDEVICE = "Device not supported"
SUCCESS = "Transaction successful"
PENDING = "Transaction pending"
FAILED = "Transaction failed"
DUPLICATE = "Duplicate transaction"
PROCESSING = "Transaction processing"
PROCCESSED = "Payment already process"
UNKNOWNUSER = "Invalid User account details"
DEVICEMISMATCH = "Please unloack your device."
INVALIDACCOUNT = "Invalid user account"
INVALIDBILLER = "Invalid biller"
INVALIDPIN="Invalid Transaction PIN"
UNABLE = "Unable to complete transaction. Try again"
INSUFFICIENTFUND = "Insufficient fund to process your transaction"
DEBITFAILED = "Unable to debit your account"
SAMEACCOUNT = "sender cannot be the same as receiver"
ALREADYEXIST = f"Account already exist! Please login to continue"
ACCTERROR = f"Account opening error"
SYSTEMBUSY = f"System busy try again later"
DEVICEINELIGIBLE = "You are not eligible for cash point transactions"
AMMISMATCHED = "Agent or Merchant has not been registered under you"
UNKNOWNTRANSACTION = "Invalid transaction"
BVNMISMATCH="Your bvn details does not match your records"
CREATEACCTERR= "Error while creating your Account."
INCOMPLETE="Unable to complete process"
ONECASHPOINTAGENT = "An agent is only entitled to one cashpoint"
QUERYALLCASHPOINT = """SELECT p.id id,p.pos_status status,p.terminalid terminalid,p.serialnumber serialnumber,
            CONCAT(rq.firstname, ',', rq.lastname) requester, CONCAT(ast.firstname, ',', ast.lastname) assignedto,
            p.current_balance current_balance,p.virtualAccount virtualAccount,
            p.purchasedAmount purchasedAmount,p.paid paid,p.isApproved isApproved,p.isActivated isActivated,p.isBlocked isBlocked,
            p.created_at createdAt,p.approved_at approvedAt FROM pos p JOIN users rq ON p.request_by = rq.id 
            JOIN users ast ON ast.id = p.assigned_to and p.request_by = <rid> order by p.created_at DESC"""
QUERYTRANSACTION = """SELECT t.id id,
t.transactionId transactionId,
t.terminalId terminalId,
t.reference reference,
t.customerBillerId customerBillerId,
t.amount amount,
t.product product,
t.transactionType transactionType,
t.transactionStatus transactionStatus,
t.recipientId recipientId,
t.recipientAccountNumber recipientAccountNumber,
t.recipientBank recipientBank,
t.recipientName recipientName,
t.senderName senderName,
t.cardRRN cardRRN,
t.cardPan cardPan,
t.cashbackFee cashbackFee,
t.serviceFee serviceFee,
t.channel channel,
t.cardPan cardPan,
t.cardPan cardPan,
t.isDebit isDebit,
t.remarks remarks,
t.status status,
CONCAT(usr.firstname, ',', usr.lastname) userName,
usr.account_type userType,
usr.business_name userBusinessName, 
CONCAT(own.firstname, ',', own.lastname) owner,
own.account_type businessType,
own.business_name businessName,
t.created_at createdAt,t.updated_at updatedAt 
FROM transactions t JOIN users usr ON t.user_id = usr.id
JOIN users own ON own.id = t.owner_id and t.user_id = <userId> order by t.created_at DESC"""
QUERYTRANSACTIONBYDATE = """SELECT t.id id,
t.transactionId transactionId,
t.terminalId terminalId,
t.reference reference,
t.customerBillerId customerBillerId,
t.amount amount,
t.product product,
t.transactionType transactionType,
t.transactionStatus transactionStatus,
t.recipientId recipientId,
t.recipientAccountNumber recipientAccountNumber,
t.recipientBank recipientBank,
t.recipientName recipientName,
t.senderName senderName,
t.cardRRN cardRRN,
t.cardPan cardPan,
t.cashbackFee cashbackFee,
t.serviceFee serviceFee,
t.channel channel,
t.cardPan cardPan,
t.cardPan cardPan,
t.isDebit isDebit,
t.remarks remarks,
t.status status,
CONCAT(usr.firstname, ',', usr.lastname) userName,
usr.account_type userType,
usr.business_name userBusinessName, 
CONCAT(own.firstname, ',', own.lastname) owner,
own.account_type businessType,
own.business_name businessName,
t.created_at createdAt,t.updated_at updatedAt 
FROM transactions t JOIN users usr ON t.user_id = usr.id
JOIN users own ON own.id = t.owner_id and t.user_id = <userId> and 
DATE_FORMAT(t.created_at,"%Y-%m-%d") >= '<start>' and DATE_FORMAT(t.created_at,"%Y-%m-%d") <= '<end>' order by t.created_at DESC
"""


QUERYTRANSACTIONS = """SELECT t.id id,
t.transactionId transactionId,
t.terminalId terminalId,
t.reference reference,
t.customerBillerId customerBillerId,
t.amount amount,
t.product product,
t.transactionType transactionType,
t.transactionStatus transactionStatus,
t.recipientId recipientId,
t.recipientAccountNumber recipientAccountNumber,
t.recipientBank recipientBank,
t.recipientName recipientName,
t.senderName senderName,
t.cardRRN cardRRN,
t.cardPan cardPan,
t.cashbackFee cashbackFee,
t.serviceFee serviceFee,
t.channel channel,
t.cardPan cardPan,
t.cardPan cardPan,
t.isDebit isDebit,
t.remarks remarks,
t.status status,
CONCAT(usr.firstname, ',', usr.lastname) userName,
usr.account_type userType,
usr.business_name userBusinessName, 
CONCAT(own.firstname, ',', own.lastname) owner,
own.account_type businessType,
own.business_name businessName,
t.created_at createdAt,t.updated_at updatedAt 
FROM transactions t JOIN users usr ON t.user_id = usr.id
JOIN users own ON own.id = t.owner_id and t.user_id = <userId> and t.transactionType is not null order by t.created_at DESC"""
QUERYTRANSACTIONBYDATEANDTRANSTYPE = """SELECT t.id id,
t.transactionId transactionId,
t.terminalId terminalId,
t.reference reference,
t.customerBillerId customerBillerId,
t.amount amount,
t.product product,
t.transactionType transactionType,
t.transactionStatus transactionStatus,
t.recipientId recipientId,
t.recipientAccountNumber recipientAccountNumber,
t.recipientBank recipientBank,
t.recipientName recipientName,
t.senderName senderName,
t.cardRRN cardRRN,
t.cardPan cardPan,
t.cashbackFee cashbackFee,
t.serviceFee serviceFee,
t.channel channel,
t.cardPan cardPan,
t.cardPan cardPan,
t.isDebit isDebit,
t.remarks remarks,
t.status status,
CONCAT(usr.firstname, ',', usr.lastname) userName,
usr.account_type userType,
usr.business_name userBusinessName, 
CONCAT(own.firstname, ',', own.lastname) owner,
own.account_type businessType,
own.business_name businessName,
t.created_at createdAt,t.updated_at updatedAt 
FROM transactions t JOIN users usr ON t.user_id = usr.id
JOIN users own ON own.id = t.owner_id and t.user_id = <userId> and 
DATE_FORMAT(t.created_at,"%Y-%m-%d") >= '<start>' and DATE_FORMAT(t.created_at,"%Y-%m-%d") <= '<end>'
and t.transactionType = '<transactionType>' order by t.created_at DESC
"""
QUERYTRANSACTIONBYDATES = """SELECT t.id id,
t.transactionId transactionId,
t.terminalId terminalId,
t.reference reference,
t.customerBillerId customerBillerId,
t.amount amount,
t.product product,
t.transactionType transactionType,
t.transactionStatus transactionStatus,
t.recipientId recipientId,
t.recipientAccountNumber recipientAccountNumber,
t.recipientBank recipientBank,
t.recipientName recipientName,
t.senderName senderName,
t.cardRRN cardRRN,
t.cardPan cardPan,
t.cashbackFee cashbackFee,
t.serviceFee serviceFee,
t.channel channel,
t.cardPan cardPan,
t.cardPan cardPan,
t.isDebit isDebit,
t.remarks remarks,
t.status status,
CONCAT(usr.firstname, ',', usr.lastname) userName,
usr.account_type userType,
usr.business_name userBusinessName, 
CONCAT(own.firstname, ',', own.lastname) owner,
own.account_type businessType,
own.business_name businessName,
t.created_at createdAt,t.updated_at updatedAt 
FROM transactions t JOIN users usr ON t.user_id = usr.id
JOIN users own ON own.id = t.owner_id and t.user_id = <userId> and 
DATE_FORMAT(t.created_at,"%Y-%m-%d") >= '<start>' and DATE_FORMAT(t.created_at,"%Y-%m-%d") <= '<end>'
and t.transactionType is not null order by t.created_at DESC
"""
QUERYSINGLETRANSACTION = """SELECT t.id id,
t.transactionId transactionId,
t.terminalId terminalId,
t.reference reference,
t.customerBillerId customerBillerId,
t.amount amount,
t.product product,
t.transactionType transactionType,
t.transactionStatus transactionStatus,
t.recipientId recipientId,
t.recipientAccountNumber recipientAccountNumber,
t.recipientBank recipientBank,
t.recipientName recipientName,
t.senderName senderName,
t.cardRRN cardRRN,
t.cardPan cardPan,
t.cashbackFee cashbackFee,
t.serviceFee serviceFee,
t.channel channel,
t.cardPan cardPan,
t.cardPan cardPan,
t.isDebit isDebit,
t.remarks remarks,
t.status status,
CONCAT(usr.firstname, ',', usr.lastname) userName,
usr.account_type userType,
usr.business_name userBusinessName, 
CONCAT(own.firstname, ',', own.lastname) owner,
own.account_type businessType,
own.business_name businessName,
t.created_at createdAt,t.updated_at updatedAt 
FROM transactions t JOIN users usr ON t.user_id = usr.id
JOIN users own ON own.id = t.owner_id and t.user_id = <userId>
and t.transactionId = '<transactionId>' order by t.created_at DESC
"""


QUERYCASHPOINTTRANSACTION = """SELECT t.id id,
t.transactionId transactionId,
t.terminalId terminalId,
t.reference reference,
t.customerBillerId customerBillerId,
t.amount amount,
t.product product,
t.transactionType transactionType,
t.transactionStatus transactionStatus,
t.recipientId recipientId,
t.recipientAccountNumber recipientAccountNumber,
t.recipientBank recipientBank,
t.recipientName recipientName,
t.senderName senderName,
t.cardRRN cardRRN,
t.cardPan cardPan,
t.cashbackFee cashbackFee,
t.serviceFee serviceFee,
t.channel channel,
t.cardPan cardPan,
t.cardPan cardPan,
t.isDebit isDebit,
t.remarks remarks,
t.status status,
CONCAT(usr.firstname, ',', usr.lastname) userName,
usr.account_type userType,
usr.business_name userBusinessName, 
CONCAT(own.firstname, ',', own.lastname) owner,
own.account_type businessType,
own.business_name businessName,
t.created_at createdAt,t.updated_at updatedAt 
FROM transactions t JOIN users usr ON t.user_id = usr.id
JOIN users own ON own.id = t.owner_id and t.user_id = <userId> and t.terminalId is not null order by t.created_at DESC """
QUERYCASHPOINTTRANSACTIONBYDATEANDTERMINAL = """SELECT t.id id,
t.transactionId transactionId,
t.terminalId terminalId,
t.reference reference,
t.customerBillerId customerBillerId,
t.amount amount,
t.product product,
t.transactionType transactionType,
t.transactionStatus transactionStatus,
t.recipientId recipientId,
t.recipientAccountNumber recipientAccountNumber,
t.recipientBank recipientBank,
t.recipientName recipientName,
t.senderName senderName,
t.cardRRN cardRRN,
t.cardPan cardPan,
t.cashbackFee cashbackFee,
t.serviceFee serviceFee,
t.channel channel,
t.cardPan cardPan,
t.cardPan cardPan,
t.isDebit isDebit,
t.remarks remarks,
t.status status,
CONCAT(usr.firstname, ',', usr.lastname) userName,
usr.account_type userType,
usr.business_name userBusinessName, 
CONCAT(own.firstname, ',', own.lastname) owner,
own.account_type businessType,
own.business_name businessName,
t.created_at createdAt,t.updated_at updatedAt 
FROM transactions t JOIN users usr ON t.user_id = usr.id
JOIN users own ON own.id = t.owner_id and t.user_id = <userId> and 
DATE_FORMAT(t.created_at,"%Y-%m-%d") >= '<start>' and DATE_FORMAT(t.created_at,"%Y-%m-%d") <= '<end>'
and t.terminalId ='<terminal>' order by t.created_at DESC
"""
QUERYCASHPOINTTRANSACTIONBYDATE = """SELECT t.id id,
t.transactionId transactionId,
t.terminalId terminalId,
t.reference reference,
t.customerBillerId customerBillerId,
t.amount amount,
t.product product,
t.transactionType transactionType,
t.transactionStatus transactionStatus,
t.recipientId recipientId,
t.recipientAccountNumber recipientAccountNumber,
t.recipientBank recipientBank,
t.recipientName recipientName,
t.senderName senderName,
t.cardRRN cardRRN,
t.cardPan cardPan,
t.cashbackFee cashbackFee,
t.serviceFee serviceFee,
t.channel channel,
t.cardPan cardPan,
t.cardPan cardPan,
t.isDebit isDebit,
t.remarks remarks,
t.status status,
CONCAT(usr.firstname, ',', usr.lastname) userName,
usr.account_type userType,
usr.business_name userBusinessName, 
CONCAT(own.firstname, ',', own.lastname) owner,
own.account_type businessType,
own.business_name businessName,
t.created_at createdAt,t.updated_at updatedAt 
FROM transactions t JOIN users usr ON t.user_id = usr.id
JOIN users own ON own.id = t.owner_id and t.user_id = <userId> and 
DATE_FORMAT(t.created_at,"%Y-%m-%d") >= '<start>' and DATE_FORMAT(t.created_at,"%Y-%m-%d") <= '<end>'
and t.terminalId is not null order by t.created_at DESC
"""
