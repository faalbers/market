YAHOO_USER_AGENT = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36'
YAHOO_USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36",
]

# modules and time schemes
QUOTESUMMARY_MODULES = {
    "summaryProfile": 60, # contains general information about the company",
    "summaryDetail": 60, # prices + volume + market cap + etc",
    "assetProfile": 60, # summaryProfile + company officers",
    "fundProfile": 60, # ",
    "price": 60, # current prices",
    "quoteType": 60, # quoteType",
    "esgScores": 60, # Environmental, social, and governance (ESG) scores, sustainability and ethical performance of companies",
    "incomeStatementHistory": 60, # ",
    "incomeStatementHistoryQuarterly": 60, # ",
    "balanceSheetHistory": 60, # ",
    "balanceSheetHistoryQuarterly": 60, # ",
    "cashFlowStatementHistory": 60, # ",
    "cashFlowStatementHistoryQuarterly": 60, # ",
    "defaultKeyStatistics": 60, # KPIs (PE, enterprise value, EPS, EBITA, and more)",
    "financialData": 60, # Financial KPIs (revenue, gross margins, operating cash flow, free cash flow, and more)",
    "calendarEvents": 60, # future earnings date",
    "secFilings": 60, # SEC filings, such as 10K and 10Q reports",
    "upgradeDowngradeHistory": 60, # upgrades and downgrades that analysts have given a company"s stock",
    "institutionOwnership": 60, # institutional ownership, holders and shares outstanding",
    "fundOwnership": 60, # mutual fund ownership, holders and shares outstanding",
    "majorDirectHolders": 60, # ",
    "majorHoldersBreakdown": 60, # ",
    "insiderTransactions": 60, # insider transactions, such as the number of shares bought and sold by company executives",
    "insiderHolders": 60, # insider holders, such as the number of shares held by company executives",
    "netSharePurchaseActivity": 60, # net share purchase activity, such as the number of shares bought and sold by company executives",
    "earnings": 60, # earnings history",
    "earningsHistory": 60, # ",
    "earningsTrend": 60, # earnings trend",
    "industryTrend": 60, # ",
    "indexTrend": 60, # ",
    "sectorTrend": 60, # ",
    "recommendationTrend": 60, # ",
    "futuresChain": 60, # ",
}

FUNDAMENTALS_PERIODTYPES = ['trailing', 'quarterly', 'annual']
FUNDAMENTALS_KEYS = {
    'financials': ["TaxEffectOfUnusualItems", "TaxRateForCalcs", "NormalizedEBITDA", "NormalizedDilutedEPS",
                   "NormalizedBasicEPS", "TotalUnusualItems", "TotalUnusualItemsExcludingGoodwill",
                   "NetIncomeFromContinuingOperationNetMinorityInterest", "ReconciledDepreciation",
                   "ReconciledCostOfRevenue", "EBITDA", "EBIT", "NetInterestIncome", "InterestExpense",
                   "InterestIncome", "ContinuingAndDiscontinuedDilutedEPS", "ContinuingAndDiscontinuedBasicEPS",
                   "NormalizedIncome", "NetIncomeFromContinuingAndDiscontinuedOperation", "TotalExpenses",
                   "RentExpenseSupplemental", "ReportedNormalizedDilutedEPS", "ReportedNormalizedBasicEPS",
                   "TotalOperatingIncomeAsReported", "DividendPerShare", "DilutedAverageShares", "BasicAverageShares",
                   "DilutedEPS", "DilutedEPSOtherGainsLosses", "TaxLossCarryforwardDilutedEPS",
                   "DilutedAccountingChange", "DilutedExtraordinary", "DilutedDiscontinuousOperations",
                   "DilutedContinuousOperations", "BasicEPS", "BasicEPSOtherGainsLosses", "TaxLossCarryforwardBasicEPS",
                   "BasicAccountingChange", "BasicExtraordinary", "BasicDiscontinuousOperations",
                   "BasicContinuousOperations", "DilutedNIAvailtoComStockholders", "AverageDilutionEarnings",
                   "NetIncomeCommonStockholders", "OtherunderPreferredStockDividend", "PreferredStockDividends",
                   "NetIncome", "MinorityInterests", "NetIncomeIncludingNoncontrollingInterests",
                   "NetIncomeFromTaxLossCarryforward", "NetIncomeExtraordinary", "NetIncomeDiscontinuousOperations",
                   "NetIncomeContinuousOperations", "EarningsFromEquityInterestNetOfTax", "TaxProvision",
                   "PretaxIncome", "OtherIncomeExpense", "OtherNonOperatingIncomeExpenses", "SpecialIncomeCharges",
                   "GainOnSaleOfPPE", "GainOnSaleOfBusiness", "OtherSpecialCharges", "WriteOff",
                   "ImpairmentOfCapitalAssets", "RestructuringAndMergernAcquisition", "SecuritiesAmortization",
                   "EarningsFromEquityInterest", "GainOnSaleOfSecurity", "NetNonOperatingInterestIncomeExpense",
                   "TotalOtherFinanceCost", "InterestExpenseNonOperating", "InterestIncomeNonOperating",
                   "OperatingIncome", "OperatingExpense", "OtherOperatingExpenses", "OtherTaxes",
                   "ProvisionForDoubtfulAccounts", "DepreciationAmortizationDepletionIncomeStatement",
                   "DepletionIncomeStatement", "DepreciationAndAmortizationInIncomeStatement", "Amortization",
                   "AmortizationOfIntangiblesIncomeStatement", "DepreciationIncomeStatement", "ResearchAndDevelopment",
                   "SellingGeneralAndAdministration", "SellingAndMarketingExpense", "GeneralAndAdministrativeExpense",
                   "OtherGandA", "InsuranceAndClaims", "RentAndLandingFees", "SalariesAndWages", "GrossProfit",
                   "CostOfRevenue", "TotalRevenue", "ExciseTaxes", "OperatingRevenue", "LossAdjustmentExpense",
                   "NetPolicyholderBenefitsAndClaims", "PolicyholderBenefitsGross", "PolicyholderBenefitsCeded",
                   "OccupancyAndEquipment", "ProfessionalExpenseAndContractServicesExpense", "OtherNonInterestExpense"],
    'balanceSheet': ["TreasurySharesNumber", "PreferredSharesNumber", "OrdinarySharesNumber", "ShareIssued", "NetDebt",
                      "TotalDebt", "TangibleBookValue", "InvestedCapital", "WorkingCapital", "NetTangibleAssets",
                      "CapitalLeaseObligations", "CommonStockEquity", "PreferredStockEquity", "TotalCapitalization",
                      "TotalEquityGrossMinorityInterest", "MinorityInterest", "StockholdersEquity",
                      "OtherEquityInterest", "GainsLossesNotAffectingRetainedEarnings", "OtherEquityAdjustments",
                      "FixedAssetsRevaluationReserve", "ForeignCurrencyTranslationAdjustments",
                      "MinimumPensionLiabilities", "UnrealizedGainLoss", "TreasuryStock", "RetainedEarnings",
                      "AdditionalPaidInCapital", "CapitalStock", "OtherCapitalStock", "CommonStock", "PreferredStock",
                      "TotalPartnershipCapital", "GeneralPartnershipCapital", "LimitedPartnershipCapital",
                      "TotalLiabilitiesNetMinorityInterest", "TotalNonCurrentLiabilitiesNetMinorityInterest",
                      "OtherNonCurrentLiabilities", "LiabilitiesHeldforSaleNonCurrent", "RestrictedCommonStock",
                      "PreferredSecuritiesOutsideStockEquity", "DerivativeProductLiabilities", "EmployeeBenefits",
                      "NonCurrentPensionAndOtherPostretirementBenefitPlans", "NonCurrentAccruedExpenses",
                      "DuetoRelatedPartiesNonCurrent", "TradeandOtherPayablesNonCurrent",
                      "NonCurrentDeferredLiabilities", "NonCurrentDeferredRevenue",
                      "NonCurrentDeferredTaxesLiabilities", "LongTermDebtAndCapitalLeaseObligation",
                      "LongTermCapitalLeaseObligation", "LongTermDebt", "LongTermProvisions", "CurrentLiabilities",
                      "OtherCurrentLiabilities", "CurrentDeferredLiabilities", "CurrentDeferredRevenue",
                      "CurrentDeferredTaxesLiabilities", "CurrentDebtAndCapitalLeaseObligation",
                      "CurrentCapitalLeaseObligation", "CurrentDebt", "OtherCurrentBorrowings", "LineOfCredit",
                      "CommercialPaper", "CurrentNotesPayable", "PensionandOtherPostRetirementBenefitPlansCurrent",
                      "CurrentProvisions", "PayablesAndAccruedExpenses", "CurrentAccruedExpenses", "InterestPayable",
                      "Payables", "OtherPayable", "DuetoRelatedPartiesCurrent", "DividendsPayable", "TotalTaxPayable",
                      "IncomeTaxPayable", "AccountsPayable", "TotalAssets", "TotalNonCurrentAssets",
                      "OtherNonCurrentAssets", "DefinedPensionBenefit", "NonCurrentPrepaidAssets",
                      "NonCurrentDeferredAssets", "NonCurrentDeferredTaxesAssets", "DuefromRelatedPartiesNonCurrent",
                      "NonCurrentNoteReceivables", "NonCurrentAccountsReceivable", "FinancialAssets",
                      "InvestmentsAndAdvances", "OtherInvestments", "InvestmentinFinancialAssets",
                      "HeldToMaturitySecurities", "AvailableForSaleSecurities",
                      "FinancialAssetsDesignatedasFairValueThroughProfitorLossTotal", "TradingSecurities",
                      "LongTermEquityInvestment", "InvestmentsinJointVenturesatCost",
                      "InvestmentsInOtherVenturesUnderEquityMethod", "InvestmentsinAssociatesatCost",
                      "InvestmentsinSubsidiariesatCost", "InvestmentProperties", "GoodwillAndOtherIntangibleAssets",
                      "OtherIntangibleAssets", "Goodwill", "NetPPE", "AccumulatedDepreciation", "GrossPPE", "Leases",
                      "ConstructionInProgress", "OtherProperties", "MachineryFurnitureEquipment",
                      "BuildingsAndImprovements", "LandAndImprovements", "Properties", "CurrentAssets",
                      "OtherCurrentAssets", "HedgingAssetsCurrent", "AssetsHeldForSaleCurrent", "CurrentDeferredAssets",
                      "CurrentDeferredTaxesAssets", "RestrictedCash", "PrepaidAssets", "Inventory",
                      "InventoriesAdjustmentsAllowances", "OtherInventories", "FinishedGoods", "WorkInProcess",
                      "RawMaterials", "Receivables", "ReceivablesAdjustmentsAllowances", "OtherReceivables",
                      "DuefromRelatedPartiesCurrent", "TaxesReceivable", "AccruedInterestReceivable", "NotesReceivable",
                      "LoansReceivable", "AccountsReceivable", "AllowanceForDoubtfulAccountsReceivable",
                      "GrossAccountsReceivable", "CashCashEquivalentsAndShortTermInvestments",
                      "OtherShortTermInvestments", "CashAndCashEquivalents", "CashEquivalents", "CashFinancial",
                      "CashCashEquivalentsAndFederalFundsSold"],
    'cashFlow': ["ForeignSales", "DomesticSales", "AdjustedGeographySegmentData", "FreeCashFlow",
                  "RepurchaseOfCapitalStock", "RepaymentOfDebt", "IssuanceOfDebt", "IssuanceOfCapitalStock",
                  "CapitalExpenditure", "InterestPaidSupplementalData", "IncomeTaxPaidSupplementalData",
                  "EndCashPosition", "OtherCashAdjustmentOutsideChangeinCash", "BeginningCashPosition",
                  "EffectOfExchangeRateChanges", "ChangesInCash", "OtherCashAdjustmentInsideChangeinCash",
                  "CashFlowFromDiscontinuedOperation", "FinancingCashFlow", "CashFromDiscontinuedFinancingActivities",
                  "CashFlowFromContinuingFinancingActivities", "NetOtherFinancingCharges", "InterestPaidCFF",
                  "ProceedsFromStockOptionExercised", "CashDividendsPaid", "PreferredStockDividendPaid",
                  "CommonStockDividendPaid", "NetPreferredStockIssuance", "PreferredStockPayments",
                  "PreferredStockIssuance", "NetCommonStockIssuance", "CommonStockPayments", "CommonStockIssuance",
                  "NetIssuancePaymentsOfDebt", "NetShortTermDebtIssuance", "ShortTermDebtPayments",
                  "ShortTermDebtIssuance", "NetLongTermDebtIssuance", "LongTermDebtPayments", "LongTermDebtIssuance",
                  "InvestingCashFlow", "CashFromDiscontinuedInvestingActivities",
                  "CashFlowFromContinuingInvestingActivities", "NetOtherInvestingChanges", "InterestReceivedCFI",
                  "DividendsReceivedCFI", "NetInvestmentPurchaseAndSale", "SaleOfInvestment", "PurchaseOfInvestment",
                  "NetInvestmentPropertiesPurchaseAndSale", "SaleOfInvestmentProperties",
                  "PurchaseOfInvestmentProperties", "NetBusinessPurchaseAndSale", "SaleOfBusiness",
                  "PurchaseOfBusiness", "NetIntangiblesPurchaseAndSale", "SaleOfIntangibles", "PurchaseOfIntangibles",
                  "NetPPEPurchaseAndSale", "SaleOfPPE", "PurchaseOfPPE", "CapitalExpenditureReported",
                  "OperatingCashFlow", "CashFromDiscontinuedOperatingActivities",
                  "CashFlowFromContinuingOperatingActivities", "TaxesRefundPaid", "InterestReceivedCFO",
                  "InterestPaidCFO", "DividendReceivedCFO", "DividendPaidCFO", "ChangeInWorkingCapital",
                  "ChangeInOtherWorkingCapital", "ChangeInOtherCurrentLiabilities", "ChangeInOtherCurrentAssets",
                  "ChangeInPayablesAndAccruedExpense", "ChangeInAccruedExpense", "ChangeInInterestPayable",
                  "ChangeInPayable", "ChangeInDividendPayable", "ChangeInAccountPayable", "ChangeInTaxPayable",
                  "ChangeInIncomeTaxPayable", "ChangeInPrepaidAssets", "ChangeInInventory", "ChangeInReceivables",
                  "ChangesInAccountReceivables", "OtherNonCashItems", "ExcessTaxBenefitFromStockBasedCompensation",
                  "StockBasedCompensation", "UnrealizedGainLossOnInvestmentSecurities", "ProvisionandWriteOffofAssets",
                  "AssetImpairmentCharge", "AmortizationOfSecurities", "DeferredTax", "DeferredIncomeTax",
                  "DepreciationAmortizationDepletion", "Depletion", "DepreciationAndAmortization",
                  "AmortizationCashFlow", "AmortizationOfIntangibles", "Depreciation", "OperatingGainsLosses",
                  "PensionAndEmployeeBenefitExpense", "EarningsLossesFromEquityInvestments",
                  "GainLossOnInvestmentSecurities", "NetForeignCurrencyExchangeGainLoss", "GainLossOnSaleOfPPE",
                  "GainLossOnSaleOfBusiness", "NetIncomeFromContinuingOperations",
                  "CashFlowsfromusedinOperatingActivitiesDirect", "TaxesRefundPaidDirect", "InterestReceivedDirect",
                  "InterestPaidDirect", "DividendsReceivedDirect", "DividendsPaidDirect", "ClassesofCashPayments",
                  "OtherCashPaymentsfromOperatingActivities", "PaymentsonBehalfofEmployees",
                  "PaymentstoSuppliersforGoodsandServices", "ClassesofCashReceiptsfromOperatingActivities",
                  "OtherCashReceiptsfromOperatingActivities", "ReceiptsfromGovernmentGrants", "ReceiptsfromCustomers"]}
