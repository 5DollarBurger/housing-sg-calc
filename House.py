import numpy as np
import copy
import os
import json

PWD = os.path.abspath(os.path.dirname(__file__))


class House:
    def __init__(self, unitPrice, reno):
        self.confDict = json.load(fp=open(f"{PWD}/conf.json", "r"))
        self.unitPrice = unitPrice
        self.reno = reno

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

    def _getMortgagePmt(self, intAnnual=0.012, termYears=30, share=1, downPmtRatio=1):
        asset = share * self.unitPrice
        downPmtShare = downPmtRatio * self.downPmt
        mortLiaShare = asset - downPmtShare
        intMonthly = (1 + intAnnual) ** (1 / 12) - 1
        termMonths = termYears * 12


if __name__ == "__main__":
    unitPrice = 1.08e6
    reno = 6e4
    ins = House(unitPrice=unitPrice, reno=reno)
    print(ins.getUpfrontCF(availCPF=0.14e6, share=0.4, downPmtRatio=0.5))