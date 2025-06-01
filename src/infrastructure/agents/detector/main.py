from src.presentation.cli.commands import setup_argparse
from src.infrastructure.config.settings import load_config
from src.application.use_cases.index_logs import index_logs
from src.application.use_cases.search_indexed_logs import search_indexed_logs
from src.application.use_cases.enrich_logs import enrich_logs
from src.application.tools.logger import logger
import sys
from  src.infrastructure.data_processing.data_preprocessor  import write_nested_data_to_csv

def main():
    """Main function."""
    try:
        # Parse command-line arguments
        args = setup_argparse()
        
        # Load configuration
        config = load_config()
        
        # Determine command to run
        if args.command == "index":
            index_logs(config, args.log_file, args.chunk_size, args.chunk_overlap)
        elif args.command == "search":
            search_indexed_logs(config, args.query, args.k)
        elif args.command == "enrich":
            enrich_logs(config, args.batch_size, args.batch_delay)
        elif args.command == "write_csv":
            # Example usage of write_nested_data_to_csv
            data = [{
  "severity": 1,
  "pretext": "WAZUH Alert",
  "title": "Windows Logon Success",
  "text": None,
  "rule_id": "60106",
  "timestamp": "2025-06-01T10:35:23.167+0100",
  "id": "1748770523.4525473",
  "all_fields": {
    "timestamp": "2025-06-01T10:35:23.167+0100",
    "rule": {
      "level": 3,
      "description": "Windows Logon Success",
      "id": "60106",
      "mitre": {
        "id": [
          "T1078"
        ],
        "tactic": [
          "Defense Evasion",
          "Persistence",
          "Privilege Escalation",
          "Initial Access"
        ],
        "technique": [
          "Valid Accounts"
        ]
      },
      "firedtimes": 11,
      "mail": False,
      "groups": [
        "windows",
        "windows_security",
        "authentication_success"
      ],
      "pci_dss": [
        "10.2.5"
      ],
      "gpg13": [
        "7.1",
        "7.2"
      ],
      "gdpr": [
        "IV_32.2"
      ],
      "hipaa": [
        "164.312.b"
      ],
      "nist_800_53": [
        "AU.14",
        "AC.9"
      ],
      "tsc": [
        "CC6.8",
        "CC7.2",
        "CC7.3"
      ]
    },
    "agent": {
      "id": "001",
      "name": "yassine",
      "ip": "192.168.0.1"
    },
    "manager": {
      "name": "SSONEDE"
    },
    "id": "1748770523.4525473",
    "decoder": {
      "name": "windows_eventchannel"
    },
    "data": {
      "win": {
        "system": {
          "providerName": "Microsoft-Windows-Security-Auditing",
          "providerGuid": "{54849625-5478-4994-a5ba-3e3b0328c30d}",
          "eventID": "4624",
          "version": "3",
          "level": "0",
          "task": "12544",
          "opcode": "0",
          "keywords": "0x8020000000000000",
          "systemTime": "2025-06-01T09:35:22.1507078Z",
          "eventRecordID": "346655",
          "processID": "1372",
          "threadID": "29660",
          "channel": "Security",
          "computer": "SSONEDE",
          "severityValue": "AUDIT_SUCCESS",
          "message": "\"An account was successfully logged on.\r\n\r\nSubject:\r\n\tSecurity ID:\t\tS-1-5-18\r\n\tAccount Name:\t\tSSONEDE$\r\n\tAccount Domain:\t\tWORKGROUP\r\n\tLogon ID:\t\t0x3E7\r\n\r\nLogon Information:\r\n\tLogon Type:\t\t5\r\n\tRestricted Admin Mode:\t-\r\n\tRemote Credential Guard:\t-\r\n\tVirtual Account:\t\tNo\r\n\tElevated Token:\t\tYes\r\n\r\nImpersonation Level:\t\tImpersonation\r\n\r\nNew Logon:\r\n\tSecurity ID:\t\tS-1-5-18\r\n\tAccount Name:\t\tSYSTEM\r\n\tAccount Domain:\t\tNT AUTHORITY\r\n\tLogon ID:\t\t0x3E7\r\n\tLinked Logon ID:\t\t0x0\r\n\tNetwork Account Name:\t-\r\n\tNetwork Account Domain:\t-\r\n\tLogon GUID:\t\t{00000000-0000-0000-0000-000000000000}\r\n\r\nProcess Information:\r\n\tProcess ID:\t\t0x540\r\n\tProcess Name:\t\tC:\\Windows\\System32\\services.exe\r\n\r\nNetwork Information:\r\n\tWorkstation Name:\t-\r\n\tSource Network Address:\t-\r\n\tSource Port:\t\t-\r\n\r\nDetailed Authentication Information:\r\n\tLogon Process:\t\tAdvapi  \r\n\tAuthentication Package:\tNegotiate\r\n\tTransited Services:\t-\r\n\tPackage Name (NTLM only):\t-\r\n\tKey Length:\t\t0\r\n\r\nThis event is generated when a logon session is created. It is generated on the computer that was accessed.\r\n\r\nThe subject fields indicate the account on the local system which requested the logon. This is most commonly a service such as the Server service, or a local process such as Winlogon.exe or Services.exe.\r\n\r\nThe logon type field indicates the kind of logon that occurred. The most common types are 2 (interactive) and 3 (network).\r\n\r\nThe New Logon fields indicate the account for whom the new logon was created, i.e. the account that was logged on.\r\n\r\nThe network fields indicate where a remote logon request originated. Workstation name is not always available and may be left blank in some cases.\r\n\r\nThe impersonation level field indicates the extent to which a process in the logon session can impersonate.\r\n\r\nThe authentication information fields provide detailed information about this specific logon request.\r\n\t- Logon GUID is a unique identifier that can be used to correlate this event with a KDC event.\r\n\t- Transited services indicate which intermediate services have participated in this logon request.\r\n\t- Package name indicates which sub-protocol was used among the NTLM protocols.\r\n\t- Key length indicates the length of the generated session key. This will be 0 if no session key was requested.\""
        },
        "eventdata": {
          "subjectUserSid": "S-1-5-18",
          "subjectUserName": "SSONEDE$",
          "subjectDomainName": "WORKGROUP",
          "subjectLogonId": "0x3e7",
          "targetUserSid": "S-1-5-18",
          "targetUserName": "SYSTEM",
          "targetDomainName": "NT AUTHORITY",
          "targetLogonId": "0x3e7",
          "logonType": "5",
          "logonProcessName": "Advapi",
          "authenticationPackageName": "Negotiate",
          "logonGuid": "{00000000-0000-0000-0000-000000000000}",
          "keyLength": "0",
          "processId": "0x540",
          "processName": "C:\\\\Windows\\\\System32\\\\services.exe",
          "impersonationLevel": "%%1833",
          "virtualAccount": "%%1843",
          "targetLinkedLogonId": "0x0",
          "elevatedToken": "%%1842"
        }
      }
    },
    "location": "EventChannel"
  }
}            ]
            output_file = "Mock_Test_Data/output.csv"
            write_nested_data_to_csv(data, output_file)
            
        else:
            # Default behavior if no command is specified
            print("Security Log Analysis Tool")
            print("=" * 50)
            print("Available commands:")
            print("  index  - Index log files")
            print("  search - Search indexed logs")
            
    except Exception as e:
        logger.error(f"Error in main function: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
