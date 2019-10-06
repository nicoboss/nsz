from Fs.File import File
import Fs.Type
from binascii import hexlify as hx, unhexlify as uhx
from enum import IntEnum
from nut import Print
from nut import Keys
#Some of this may have changed in 7.x.x+

class NacpLanguageType(IntEnum):
	AmericanEnglish = 0
	BritishEnglish = 1
	Japanese = 2
	French = 3
	German = 4
	LatinAmericanSpanish = 5
	Spanish = 6
	Italian = 7
	Dutch = 8
	CanadianFrench = 9
	Portuguese = 10
	Russian = 11
	Korean = 12
	TraditionalChinese = 13
	SimplifiedChinese = 14
		
class NacpLanguage:
	def __init__(self):
		self.name = None
		self.publisher = None
		
		
class OrganizationType(IntEnum):
	CERO = 0
	GRACGCRB = 1
	GSRMR = 2
	ESRB = 3
	ClassInd = 4
	USK = 5
	PEGI = 6
	PEGIPortugal = 7
	PEGIBBFC = 8
	Russian = 9
	ACB = 10
	OFLC = 11
	
class RatingAge:
	def __init__(self):
		self.age = None


class Nacp(File):
	def __init__(self, path = None, mode = None, cryptoType = -1, cryptoKey = -1, cryptoCounter = -1):
		super(Nacp, self).__init__(path, mode, cryptoType, cryptoKey, cryptoCounter)
		
		
		self.languages = []
		
		for i in range(15):
			self.languages.append(NacpLanguage())
			
		self.isbn = None
		self.startupUserAccount = None
		self.userAccountSwitchLock = None
		self.addOnContentRegistrationType = None
		self.attribute = None
		self.parentalControl = None
		self.screenshot = None
		self.videoCapture = None
		self.dataLossConfirmation = None
		self.playLogPolicy = None
		self.presenceGroupId = None
		
		self.ages = []
		
		for i in range(12):
			self.ages.append(RatingAge())
			
		self.displayVersion = None
		self.addOnContentBaseId = None
		self.saveDataOwnerId = None
		self.userAccountSaveDataSize = None
		self.userAccountSaveDataJournalSize = None
		self.deviceSaveDataSize = None
		self.deviceSaveDataJournalSize = None
		self.bcatDeliveryCacheStorageSize = None
		self.applicationErrorCodeCategory = None
		self.localCommunicationId = None
		self.logoType = None
		self.logoHandling = None
		self.runtimeAddOnContentInstall = None
		self.crashReport = None
		self.hdcp = None
		self.seedForPseudoDeviceId = None
		self.bcatPassphrase = None
		self.userAccountSaveDataSizeMax = None
		self.userAccountSaveDataJournalSizeMax = None
		self.deviceSaveDataSizeMax = None
		self.deviceSaveDataJournalSizeMax = None
		self.temporaryStorageSize = None
		self.cacheStorageSize = None
		self.cacheStorageJournalSize = None
		self.cacheStorageDataAndJournalSizeMax = None
		self.cacheStorageIndexMax = None
		self.playLogQueryableApplicationId = None
		self.playLogQueryCapability = None
		self.repair = None
		self.programIndex = None
		self.requiredNetworkServiceLicenseOnLaunch = None
		
		
	def getName(self, i):
		self.seek(i * 0x300)
		self.languages[i].name = self.read(0x200)
		self.languages[i].name = self.languages[i].name.split(b'\0', 1)[0].decode('utf-8')
		return self.languages[i].name
		
		
	def getPublisher(self, i):
		self.seek(i * 0x300 + 0x200)
		self.languages[i].publisher = self.read(0x100)
		self.languages[i].publisher = self.languages[i].publisher.split(b'\0', 1)[0].decode('utf-8')
		return self.languages[i].publisher
		
		
	def getIsbn(self):
		self.seek(0x3000)
		self.isbn = self.read(0x24).split(b'\0', 1)[0].decode('utf-8')
		return self.isbn
		
		
	def getStartupUserAccount(self):
		self.seek(0x3025)
		b = self.readInt8('little')
		if b == 0:
			self.startupUserAccount = 'None'
		elif b == 1:
			self.startupUserAccount = 'Required'
		elif b == 2:
			self.startupUserAccount = 'RequiredWithNetworkServiceAccountAvailable'
		else:
			self.startupUserAccount = 'Unknown'
		return self.startupUserAccount
		
		
	def getUserAccountSwitchLock(self):
		self.seek(0x3026)
		b = self.readInt8('little')
		if b == 0:
			self.userAccountSwitchLock = 'Disable'
		elif b == 1:
			self.userAccountSwitchLock = 'Enable'
		else:
			self.userAccountSwitchLock = 'Unknown'
		return self.userAccountSwitchLock
		
		
	def getAddOnContentRegistrationType(self):
		self.seek(0x3027)
		b = self.readInt8('little')
		if b == 0:
			self.addOnContentRegistrationType = 'AllOnLaunch'
		elif b == 1:
			self.addOnContentRegistrationType = 'OnDemand'
		else:
			self.addOnContentRegistrationType = 'Unknown'
		return self.addOnContentRegistrationType
		
		
	def getAttribute(self):
		self.seek(0x3028)
		b = self.readInt8('little')
		if b == 0:
			self.attribute = 'None'
		elif b == 1:
			self.attribute = 'Demo'
		elif b == 2:
			self.attribute = 'RetailInteractiveDisplay'
		else:
			self.attribute = 'Unknown'
		return self.attribute
		
		
	def getParentalControl(self):
		self.seek(0x3030)
		b = self.readInt8('little')
		if b == 0:
			self.parentalControl = 'None'
		elif b == 1:
			self.parentalControl = 'FreeCommunication'
		else:
			self.parentalControl = 'Unknown'
		return self.parentalControl
		
		
	def getScreenshot(self):
		self.seek(0x3034)
		b = self.readInt8('little')
		if b == 0:
			self.screenshot = 'Allow'
		elif b == 1:
			self.screenshot = 'Deny'
		else:
			self.screenshot = 'Unknown'
		return self.screenshot
		
		
	def getVideoCapture(self):
		self.seek(0x3035)
		b = self.readInt8('little')
		if b == 0:
			self.videoCapture = 'Disable'
		elif b == 1:
			self.videoCapture = 'Manual'
		elif b == 2:
			self.videoCapture = 'Enable'
		else:
			self.videoCapture = 'Unknown'
		return self.videoCapture
		
		
	def getDataLossConfirmation(self):
		self.seek(0x3036)
		b = self.readInt8('little')
		if b == 0:
			self.dataLossConfirmation = 'None'
		elif b == 1:
			self.dataLossConfirmation = 'Required'
		else:
			self.dataLossConfirmation = 'Unknown'
		return self.dataLossConfirmation
		
		
	def getPlayLogPolicy(self):
		self.seek(0x3037)
		b = self.readInt8('little')
		if b == 0:
			self.playLogPolicy = 'All'
		elif b == 1:
			self.playLogPolicy = 'LogOnly'
		elif b == 2:
			self.playLogPolicy = 'None'
		else:
			self.playLogPolicy = 'Unknown'
		return self.playLogPolicy
		
		
	def getPresenceGroupId(self):
		self.seek(0x3038)
		self.presenceGroupId = self.readInt64('little')
		return self.presenceGroupId
		
		
	def getRatingAge(self, i):
		self.seek(i + 0x3040)
		b = self.readInt8('little')
		if b == 0:
			self.ages[i].age = '0'
		elif b == 3:
			self.ages[i].age = '3'
		elif b == 4:
			self.ages[i].age = '4'
		elif b == 6:
			self.ages[i].age = '6'
		elif b == 7:
			self.ages[i].age = '7'
		elif b == 8:
			self.ages[i].age = '8'
		elif b == 10:
			self.ages[i].age = '10'
		elif b == 12:
			self.ages[i].age = '12'
		elif b == 13:
			self.ages[i].age = '13'
		elif b == 14:
			self.ages[i].age = '14'
		elif b == 15:
			self.ages[i].age = '15'
		elif b == 16:
			self.ages[i].age = '16'
		elif b == 17:
			self.ages[i].age = '17'
		elif b == 18:
			self.ages[i].age = '18'
		else:
			self.ages[i].age = 'Unknown'
		return self.ages[i].age
		
		
	def getDisplayVersion(self):
		self.seek(0x3060)
		self.displayVersion = self.read(0xF)
		self.displayVersion = self.displayVersion.split(b'\0', 1)[0].decode('utf-8')
		return self.displayVersion
		
		
	def getAddOnContentBaseId(self):
		self.seek(0x3070)
		self.addOnContentBaseId = self.readInt64('little')
		return self.addOnContentBaseId

		
	def getSaveDataOwnerId(self):
		self.seek(0x3078)
		self.saveDataOwnerId = self.readInt64('little')
		return self.saveDataOwnerId
		
		
	def getUserAccountSaveDataSize(self):
		self.seek(0x3080)
		self.userAccountSaveDataSize = self.readInt64('little')
		return self.userAccountSaveDataSize
		
	
	def getUserAccountSaveDataJournalSize(self):
		self.seek(0x3088)
		self.userAccountSaveDataJournalSize = self.readInt64('little')
		return self.userAccountSaveDataJournalSize
		
		
	def getDeviceSaveDataSize(self):
		self.seek(0x3090)
		self.deviceSaveDataSize = self.readInt64('little')
		return self.deviceSaveDataSize
		
		
	def getDeviceSaveDataJournalSize(self):
		self.seek(0x3098)
		self.deviceSaveDataJournalSize = self.readInt64('little')
		return self.deviceSaveDataJournalSize
		
		
	def getBcatDeliveryCacheStorageSize(self):
		self.seek(0x30A0)
		self.bcatDeliveryCacheStorageSize = self.readInt64('little')
		return self.bcatDeliveryCacheStorageSize
		
		
	def getApplicationErrorCodeCategory(self):
		self.seek(0x30A8)
		self.applicationErrorCodeCategory = self.read(0x7).split(b'\0', 1)[0].decode('utf-8')
		return self.applicationErrorCodeCategory
		
		
	def getLocalCommunicationId(self):
		self.seek(0x30B0)
		self.localCommunicationId = self.readInt64('little')
		return self.localCommunicationId

		
	def getLogoType(self):
		self.seek(0x30F0)
		b = self.readInt8('little')
		if b == 0:
			self.logoType = 'LicensedByNintendo'
		elif b == 2:
			self.logoType = 'Nintendo'
		else:
			self.logoType = 'Unknown'
		return self.logoType
		
		
	def getLogoHandling(self):
		self.seek(0x30F1)
		b = self.readInt8('little')
		if b == 0:
			self.logoHandling = 'Auto'
		elif b == 1:
			self.logoHandling = 'Manual'
		else:
			self.logoHandling = 'Unknown'
		return self.logoHandling
		
		
	def getRuntimeAddOnContentInstall(self):
		self.seek(0x30F2)
		b = self.readInt8('little')
		if b == 0:
			self.runtimeAddOnContentInstall = 'Deny'
		elif b == 1:
			self.runtimeAddOnContentInstall = 'AllowAppend'
		else:
			self.runtimeAddOnContentInstall = 'Unknown'
		return self.runtimeAddOnContentInstall
		
		
	def getCrashReport(self):
		self.seek(0x30F6)
		b = self.readInt8('little')
		if b == 0:
			self.crashReport = 'Deny'
		elif b == 1:
			self.crashReport = 'Allow'
		else:
			self.crashReport = 'Unknown'
		return self.crashReport
		
		
	def getHdcp(self):
		self.seek(0x30F7)
		b = self.readInt8('little')
		if b == 0:
			self.hdcp = 'None'
		elif b == 1:
			self.hdcp = 'Required'
		else:
			self.hdcp = 'Unknown'
		return self.hdcp
		
		
	def getSeedForPseudoDeviceId(self):
		self.seek(0x30F8)
		self.seedForPseudoDeviceId = self.readInt64('little')
		return self.seedForPseudoDeviceId
		
		
	def getBcatPassphrase(self):
		self.seek(0x3100)
		self.bcatPassphrase = self.read(0x40).split(b'\0', 1)[0].decode('utf-8')
		return self.bcatPassphrase
		
		
	def getUserAccountSaveDataSizeMax(self):
		self.seek(0x3148)
		self.userAccountSaveDataSizeMax = self.readInt64('little')
		return self.userAccountSaveDataSizeMax
		
		
	def getUserAccountSaveDataJournalSizeMax(self):
		self.seek(0x3150)
		self.userAccountSaveDataJournalSizeMax = self.readInt64('little')
		return self.userAccountSaveDataJournalSizeMax
		
		
	def getDeviceSaveDataSizeMax(self):
		self.seek(0x3158)
		self.deviceSaveDataSizeMax = self.readInt64('little')
		return self.deviceSaveDataSizeMax
		
		
	def getDeviceSaveDataJournalSizeMax(self):
		self.seek(0x3160)
		self.deviceSaveDataJournalSizeMax = self.readInt64('little')
		return self.deviceSaveDataJournalSizeMax
		
		
	def getTemporaryStorageSize(self):
		self.seek(0x3168)
		self.temporaryStorageSize = self.readInt64('little')
		return self.temporaryStorageSize
		
		
	def getCacheStorageSize(self):
		self.seek(0x3170)
		self.cacheStorageSize = self.readInt64('little')
		return self.cacheStorageSize
		
		
	def getCacheStorageJournalSize(self):
		self.seek(0x3178)
		self.cacheStorageJournalSize = self.readInt64('little')
		return self.cacheStorageJournalSize
		
		
	def getCacheStorageDataAndJournalSizeMax(self):
		self.seek(0x3180)
		self.cacheStorageDataAndJournalSizeMax = self.readInt32('little')
		return self.cacheStorageDataAndJournalSizeMax
		
		
	def getCacheStorageIndexMax(self):
		self.seek(0x3188)
		self.cacheStorageIndexMax = self.readInt16('little')
		return self.cacheStorageIndexMax
		
		
	def getPlayLogQueryableApplicationId(self):
		self.seek(0x3190)
		self.playLogQueryableApplicationId = self.readInt64('little')
		return self.playLogQueryableApplicationId
		
		
	def getPlayLogQueryCapability(self):
		self.seek(0x3210)
		b = self.readInt8('little')
		if b == 0:
			self.playLogQueryCapability = 'None'
		elif b == 1:
			self.playLogQueryCapability = 'WhiteList'
		elif b == 2:
			self.playLogQueryCapability = 'All'
		else:
			self.playLogQueryCapability = 'Unknown'
		return self.playLogQueryCapability
			
	
	def getRepair(self):
		self.seek(0x3211)
		b = self.readInt8('little')
		if b == 0:
			self.repair = 'None'
		elif b == 1:
			self.repair = 'SuppressGameCardAccess'
		else:
			self.repair = 'Unknown'
		return self.repair
		
		
	def getProgramIndex(self):
		self.seek(0x3212)
		self.programIndex = self.readInt8('little')
		return self.programIndex
		
		
	def getRequiredNetworkServiceLicenseOnLaunch(self):
		self.seek(0x3213)
		b = self.readInt8('little')
		if b == 0:
			self.requiredNetworkServiceLicenseOnLaunch = 'None'
		elif b == 1:
			self.requiredNetworkServiceLicenseOnLaunch = 'Common'
		else:
			self.requiredNetworkServiceLicenseOnLaunch = 'Unknown'
		return self.requiredNetworkServiceLicenseOnLaunch
		

	def printInfo(self, indent = 0):
		tabs = '\t' * indent
		Print.info('\n%sNintendo Application Control Property (NACP)\n' % (tabs))
		super(Nacp, self).printInfo(indent)
		
		for i in range(15):
			if self.getName(i) == '':
				pass
			else:
				Print.info('Title:')
				Print.info('  Language: ' + str(NacpLanguageType(i)).replace('NacpLanguageType.', ''))
				Print.info('  Name: ' + self.getName(i))
				Print.info('  Publisher: ' + self.getPublisher(i))
			
		if str(self.getIsbn()) == '':
			 pass
		else:
			Print.info('Isbn: ' + str(self.getIsbn()))
			
		Print.info('AddOnContentRegistrationType: ' + str(self.getAddOnContentRegistrationType()))
		Print.info('StartupUserAccount: ' + str(self.getStartupUserAccount()))
		Print.info('UserAccountSwitchLock: ' + str(self.getUserAccountSwitchLock()))
		Print.info('Attribute: ' + str(self.getAttribute()))
		Print.info('ParentalControl: ' + str(self.getParentalControl()))
		Print.info('Screenshot: ' + str(self.getScreenshot()))
		Print.info('VideoCapture: ' + str(self.getVideoCapture()))
		Print.info('DataLossConfirmation: ' + str(self.getDataLossConfirmation()))
		Print.info('PlayLogPolicy: ' + str(self.getPlayLogPolicy()))
		Print.info('PresenceGroupId: ' + '0x' + hex(self.getPresenceGroupId()).replace('0x', '').zfill(16))
		
		for i in range(12):
			if str(self.getRatingAge(i)) == 'Unknown':
				pass
			else:
				Print.info('Rating:')
				Print.info('  Organization: ' + str(OrganizationType(i)).replace('OrganizationType.', ''))
				Print.info('  Age: ' + str(self.getRatingAge(i)))
			
		Print.info('DisplayVersion: ' + str(self.getDisplayVersion()))
		Print.info('AddOnContentBaseId: ' + '0x' + hex(self.getAddOnContentBaseId()).replace('0x', '').zfill(16))
		Print.info('SaveDataOwnerId: ' + '0x' + hex(self.getSaveDataOwnerId()).replace('0x', '').zfill(16))
		Print.info('UserAccountSaveDataSize: ' + '0x' + hex(self.getUserAccountSaveDataSize()).replace('0x', '').zfill(16))
		Print.info('UserAccountSaveDataJournalSize: ' + '0x' + hex(self.getUserAccountSaveDataJournalSize()).replace('0x', '').zfill(16))
		Print.info('DeviceSaveDataSize: ' + '0x' + hex(self.getDeviceSaveDataSize()).replace('0x', '').zfill(16))
		Print.info('DeviceSaveDataJournalSize: ' + '0x' + hex(self.getDeviceSaveDataJournalSize()).replace('0x', '').zfill(16))
		
		if hex(self.getBcatDeliveryCacheStorageSize()).replace('0x', '').zfill(16) == '0000000000000000':
			pass
		else:
			Print.info('BcatDeliveryCacheStorageSize: ' + '0x' + hex(self.getBcatDeliveryCacheStorageSize()).replace('0x', '').zfill(16))
			
		if str(self.getApplicationErrorCodeCategory()) == '':
			pass
		else:
			Print.info('ApplicationErrorCodeCategory: ' + str(self.getApplicationErrorCodeCategory()))
			
		Print.info('LocalCommunicationId: ' + '0x' + hex(self.getLocalCommunicationId()).replace('0x', '').zfill(16))
		Print.info('LogoType: ' + str(self.getLogoType()))
		Print.info('LogoHandling: ' + str(self.getLogoHandling()))
		Print.info('RuntimeAddOnContentInstall: ' + str(self.getRuntimeAddOnContentInstall()))
		Print.info('CrashReport: ' + str(self.getCrashReport()))
		Print.info('Hdcp: ' + str(self.getHdcp()))
		Print.info('SeedForPseudoDeviceId: ' + '0x' + hex(self.getSeedForPseudoDeviceId()).replace('0x', '').zfill(16))
		
		if str(self.getBcatPassphrase()) == '0000000000000000000000000000000000000000000000000000000000000000':
			pass
		elif str(self.getBcatPassphrase()) == '':
			pass
		else:
			Print.info('BcatPassphrase: ' + str(self.getBcatPassphrase()))
			
		Print.info('UserAccountSaveDataSizeMax: ' + '0x' + hex(self.getUserAccountSaveDataSizeMax()).replace('0x', '').zfill(16))
		Print.info('UserAccountSaveDataJournalSizeMax: ' + '0x' + hex(self.getUserAccountSaveDataJournalSizeMax()).replace('0x', '').zfill(16))
		Print.info('DeviceSaveDataSizeMax: ' + '0x' + hex(self.getDeviceSaveDataSizeMax()).replace('0x', '').zfill(16))
		Print.info('DeviceSaveDataJournalSizeMax: ' + '0x' + hex(self.getDeviceSaveDataJournalSizeMax()).replace('0x', '').zfill(16))
		Print.info('TemporaryStorageSize: ' + '0x' + hex(self.getTemporaryStorageSize()).replace('0x', '').zfill(16))
		Print.info('CacheStorageSize: ' + '0x' + hex(self.getCacheStorageSize()).replace('0x', '').zfill(16))
		Print.info('CacheStorageJournalSize: ' + '0x' + hex(self.getCacheStorageJournalSize()).replace('0x', '').zfill(16))
		Print.info('CacheStorageDataAndJournalSizeMax: ' + '0x' + hex(self.getCacheStorageDataAndJournalSizeMax()).replace('0x', '').zfill(8))
		Print.info('CacheStorageIndexMax: ' + '0x' + hex(self.getCacheStorageIndexMax()).replace('0x', '').zfill(4))
		Print.info('PlayLogQueryableApplicationId: ' + '0x' + hex(self.getPlayLogQueryableApplicationId()).replace('0x', '').zfill(16))
		Print.info('PlayLogQueryCapability: ' + str(self.getPlayLogQueryCapability()))
		Print.info('Repair: ' + str(self.getRepair()))
		Print.info('ProgramIndex: ' + str(self.getProgramIndex()))
		Print.info('RequiredNetworkServiceLicenseOnLaunch: ' + str(self.getRequiredNetworkServiceLicenseOnLaunch()))
