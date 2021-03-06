import numpy_financial as npf
import copy
import os
import json

PWD = os.path.abspath(os.path.dirname(__file__))


class House:
    def __init__(self, unitPrice, reno, mortInt, mortTerm):
        self.confDict = json.load(fp=open(f"{PWD}/conf.json", "r"))
        self.unitPrice = unitPrice
        self.reno = reno
        self.mortInt = mortInt
        self.mortTerm = mortTerm

        self.downPmt = self.confDict["downPmtPortion"] * unitPrice
        self.mortgageLiability = unitPrice - self.downPmt

    def _getStampDuty(self):
        priceBalance = copy.copy(self.unitPrice)
        stampDuty = 0
        priceLo = 0
        for k, v in self.confDict["stampDuty"].items():
            priceHi = int(k)
            costBasis = min(priceHi - priceLo, priceBalance)
            comp = costBasis * v
            stampDuty += comp
            priceBalance -= costBasis
            priceBalance = max(priceBalance, 0)
            priceLo = priceHi
        return stampDuty

    def _getNonDownPmtUpfront(self):
        legalFees = self.confDict["legalFees"]
        return legalFees + self.reno + self._getStampDuty()

    def getUpfrontCF(self, availCPF, share=1, downPmtRatio=1):
        downPmtShare = downPmtRatio * self.downPmt
        downPmtCPF = min(availCPF, downPmtShare)
        downPmtCF = max(downPmtShare - downPmtCPF, 0)

        nonDownPmtShare = share * self._getNonDownPmtUpfront()
        return downPmtCF + nonDownPmtShare

    def _getAnnualPmt(self, principal, intAnnual, termYears):
        intMonthly = (1 + intAnnual) ** (1 / 12) - 1
        termMonths = termYears * 12
        pmtMonthly = -npf.pmt(rate=intMonthly, nper=termMonths, pv=principal, fv=0, when="begin")
        return pmtMonthly * 12

    def _getMortLia(self, share, downPmtRatio, addloan):
        asset = share * self.unitPrice
        downPmtShare = downPmtRatio * self.downPmt
        mortLiaShare = asset - downPmtShare - addloan
        return mortLiaShare

    def getAnnualCF(self, availCPF, share=1, downPmtRatio=1, addloan=0, addInt=0.02, addTerm=10):
        mortLiaShare = self._getMortLia(share=share, downPmtRatio=downPmtRatio, addloan=addloan)
        mortCF = self._getAnnualPmt(principal=mortLiaShare, intAnnual=self.mortInt, termYears=self.mortTerm)
        addCF = self._getAnnualPmt(principal=addloan, intAnnual=addInt, termYears=addTerm)
        return max(mortCF + addCF - availCPF, 0)

    def _getAssetFV(self, years, ror, share=1):
        FVIF = (1 + ror) ** years
        return FVIF * share * self.unitPrice

    def getCashReturn(self, availCPFUpfront, availCPFAnnual, years, ror, share=1):
        assetFV = self._getAssetFV(years=years, ror=ror, share=share)
        cpfFV = -npf.fv(rate=self.confDict["cpfReturn"], nper=years, pmt=availCPFAnnual,
                        pv=availCPFUpfront, when="begin")

    # def getLiabilityFV(self, years, share=1, downPmtRatio=1, addloan=0, addInt=0.02):
    #     asset = share * self.unitPrice
    #     downPmtShare = downPmtRatio * self.downPmt
    #     mortLiaShare = asset - downPmtShare - addloan



if __name__ == "__main__":
    unitPrice = 1.08e6
    reno = 6e4
    mortInt = 0.015
    mortTerm = 30
    share = 0.04
    downPmtRatio = 0.5
    ins = House(unitPrice=unitPrice, reno=reno, mortInt=mortInt, mortTerm=mortTerm)
    upfrontCF = ins.getUpfrontCF(availCPF=0.14e6, share=share, downPmtRatio=downPmtRatio)
    print("Upfront cashflow: %.2f" % upfrontCF)
    annualCF = ins.getAnnualCF(availCPF=9600, share=share, downPmtRatio=downPmtRatio)
    print("Annual cashflow: %.2f" % annualCF)
    cashReturn = ins.getAssetReturn(years=6, ror=0.04, share=share)