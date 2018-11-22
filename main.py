import pandas as pd
from cobra.mit.access import MoDirectory
from cobra.mit.session import LoginSession
from cobra.mit.request import ConfigRequest
from cobra.model.fv import Tenant, Ctx, BD, RsCtx, RsBDToOut, Ap, AEPg, RsBd, RsDomAtt, RsPathAtt
from cobra.model.vmm import SecP
from cobra.internal.codec.jsoncodec import toJSONStr
import requests.packages.urllib3
requests.packages.urllib3.disable_warnings()


def apic_logon():
    apicUrl = 'https://192.168.2.79'
    loginSession = LoginSession(apicUrl, 'admin', 'C1sc0123')
    moDir = MoDirectory(loginSession)
    moDir.login()
    # Use the connected moDir queries and configuration...
    #moDir.logout()
    return moDir


def class_lookup(lookuptype='class', moclass='polUni', modn='uni'):
    if lookuptype == 'class':
        uniMo = moDir.lookupByClass(moclass)
    elif lookuptype == 'dn':
        uniMo = moDir.lookupByDn(modn)
    return uniMo


def create_tenants(delete=''):
    tenant_df = pd.read_excel("input-data/ACI_DD_Workbook.xlsx", sheet_name='Tenants')
    file = open("Tenant_Configuration.log","w")
    logon = apic_logon()
    uniMo = logon.lookupByDn('uni')
    for index, row in tenant_df.iterrows():
        fvTenant = Tenant(uniMo, name=row["Tenant Name"], description=row["Tenant Description"])
        cfgRequest = ConfigRequest()
        if delete == 'yes':
            fvTenant = Tenant(uniMo, name=row["Tenant Name"], status='deleted')
            cfgRequest.addMo(fvTenant)
        else:
            cfgRequest.addMo(fvTenant)
        logon.commit(cfgRequest)
        json_data= toJSONStr(fvTenant, prettyPrint=True)
        file.write('\n-------------------------------------------------------------------\n')
        file.write(json_data)
    file.close()


def create_vrfs(delete=''):
    vrf_df = pd.read_excel("input-data/ACI_DD_Workbook.xlsx", sheet_name='VRFs')
    file = open("VRF_Configuration.log", "w")
    logon = apic_logon()
    uniMo = logon.lookupByDn('uni')
    for index, row in vrf_df.iterrows():
        fvTenant = Tenant(uniMo, row['Tenant'])
        if delete == 'yes':
            fvCtx = Ctx(fvTenant,
                        name=row['Name'],
                        status='deleted')
        else:

            fvCtx =Ctx(fvTenant,
                       name=row['Name'],
                       pcEnfDir=row['Enforcement Direction'],
                       pcEndPref=row['Enforcement'],
                       description=row['Description'])
        cfgRequest = ConfigRequest()
        cfgRequest.addMo(fvCtx)
        logon.commit(cfgRequest)
        json_data = toJSONStr(fvCtx, prettyPrint=True)
        file.write('\n-------------------------------------------------------------------\n')
        file.write(json_data)
    file.close()


def create_bridge_domains(delete=''):
    bd_df = pd.read_excel("input-data/ACI_DD_Workbook.xlsx", sheet_name='Bridge_Domains')
    file = open("BD_Configuration.log", "w")
    logon = apic_logon()
    uniMo = logon.lookupByDn('uni')
    for index, row in bd_df.iterrows():
        fvTenant = Tenant(uniMo, row['Tenant'])
        if delete == 'yes':
            fvBD = BD(fvTenant,
                        name=row['Name'],
                        status='deleted')
        else:
            fvBD = BD(fvTenant,
                      name=row['Name'],
                      arpFlood=row['ARP Flood'],
                      ipLearning=row['EP_learn'],
                      description=row['Description'],
                      multiDstPktAct=row['MultiDest_Flood'],
                      mcastAllow=row['mcastAllow'],
                      unkMcastAct=row['L3Unk_Mcast'],
                      limitIpLearnToSubnets=row['Limit_IP_Learn'])
            fvRsCtx = RsCtx(fvBD, tnFvCtxName=row['VRF'])
            if pd.isnull(row['L3O']) == False:
                fvRsBDToOut = RsBDToOut(fvBD, tnL3extOutName=row['L3O'])
        cfgRequest = ConfigRequest()
        cfgRequest.addMo(fvBD)
        logon.commit(cfgRequest)
        json_data = toJSONStr(fvBD, prettyPrint=True)
        file.write('\n-------------------------------------------------------------------\n')
        file.write(json_data)
    file.close()

def create_endpoint_groups(delete=''):
    epg_df = pd.read_excel("input-data/ACI_DD_Workbook.xlsx", sheet_name='End_Point_Groups')
    file = open("EPG_Configuration.log", "w")
    logon = apic_logon()
    uniMo = logon.lookupByDn('uni')
    for index, row in epg_df.iterrows():
        fvTenant = Tenant(uniMo, row['Tenant'])
        fvAp = Ap(fvTenant, row['Application Profile'])
        if delete == 'yes':
            fvAEPg = AEPg(fvAp,
                        name=row['Name'],
                        status='deleted')
        else:
            fvAEPg = AEPg(fvAp,
                      name=row['EPG Name'],
                      description=row['EPG Description'],
                      prefGrMemb=row['prefGrMemb'])
            if pd.isnull(row['Associated Bridge Domain']) == False:
                fvRsBD = RsBd(fvAEPg, tnFvBDName=row['Associated Bridge Domain'])
            if pd.isnull(row['Physical Domain']) == False:
                fvRsDomAtt = RsDomAtt(fvAEPg, tDn='uni/phys-%s' % row['Physical Domain'])
            if pd.isnull(row['Static Path']) == False:
                fvRsPathAtt = RsPathAtt(fvAEPg, tDn=row['Static Path'], encap='vlan-%s' % row['VLAN Encap'])
            if pd.isnull(row['Associated VMM1']) == False:
                fvRsDomAtt1 = RsDomAtt(fvAEPg, tDn='uni/vmmp-VMware/dom-' + row['Associated VMM1'],
                                                      primaryEncap=u'unknown',
                                                      classPref=u'encap', delimiter=u'', instrImedcy=u'lazy',
                                                      encap=u'unknown', encapMode=u'auto', resImedcy=u'immediate')
                vmmSecP = SecP(fvRsDomAtt1, ownerKey=u'', name=u'', descr=u'',
                                               forgedTransmits=u'reject',
                                               ownerTag=u'', allowPromiscuous=u'reject', macChanges=u'reject')
            if pd.isnull(row['Associated VMM2']) == False:
                fvRsDomAtt2 = RsDomAtt(fvAEPg, tDn='uni/vmmp-VMware/dom-' + row['Associated VMM2'],
                                                      primaryEncap=u'unknown',
                                                      classPref=u'encap', delimiter=u'', instrImedcy=u'lazy',
                                                      encap=u'unknown', encapMode=u'auto', resImedcy=u'immediate')
                vmmSecP2 = SecP(fvRsDomAtt2, ownerKey=u'', name=u'', descr=u'',
                                                forgedTransmits=u'reject',
                                                ownerTag=u'', allowPromiscuous=u'reject', macChanges=u'reject')
        cfgRequest = ConfigRequest()
        cfgRequest.addMo(fvAp)
        logon.commit(cfgRequest)
        json_data = toJSONStr(fvAp, prettyPrint=True)
        file.write('\n-------------------------------------------------------------------\n')
        file.write(json_data)
    file.close()


create_tenants()
create_vrfs()
create_bridge_domains()
create_endpoint_groups()