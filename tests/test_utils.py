import os
import tempfile
import yaml


def write_temp_kubeconfig():
    """Generate kubeconfig in tmp
    :return: return path to temporary kubeconfig file
    """
    kubeconfig_data = generate_dump_config()
    temp_fd, temp_path = tempfile.mkstemp()
    with os.fdopen(temp_fd, 'w') as temp_file:
        temp_file.write(kubeconfig_data)
    return temp_path


def generate_dump_config():
    """Generate unit test kube config
    :return:
    """
    return """
apiVersion: v1
clusters:
- cluster:
    certificate-authority-data: LS0tLS1CRUdJTiBDRVJUSUZJQ0FURS0tLS0tCk1JSUM2akNDQWRLZ0F3SUJBZ0lCQURBTkJna3Foa2lHOXcwQkFRc0ZBREFWTVJNd0VRWURWUVFERXdwcmRXSmwKY201bGRHVnpNQjRYRFRJek1USXdOekE1TVRrME1Gb1hEVE16TVRJd05EQTVNalEwTUZvd0ZURVRNQkVHQTFVRQpBeE1LYTNWaVpYSnVaWFJsY3pDQ0FTSXdEUVlKS29aSWh2Y05BUUVCQlFBRGdnRVBBRENDQVFvQ2dnRUJBTjUzCmQwcjJrVGI5YmRKSjlRWmp2d2FJVEdVd3JRWUtFc2p1amdiZXRjZDZxSGlZUjFNdTNjSXVORWh1VnB3MkRrV1oKZ3dtMHpiV1JaNXFxbVVCODBiTWpHbFk0YnBkRExUcEl1OCtkRmlwOHo0VjMyY3VqZXRadEMyd2gyYStycnZsagpDUWZDTnJvU2NUYnhiNGRlVGt0bGtONUs4ZEMwWkg2NlpKWklNcmd3YytwMkJZTjNFeGxMSmwwZ21HZkNTMnB1CjFOcFgzUmJKbFZVQ3gwb2VTekI3ZEtqb0wzS0J4eUZRRTBYSllmeEhZd1Z1U3VTd3BUU1BwbWcwTzlHc0tQV0kKUnZ2ZStaWHdlNGVHN1BMYlhtZWhXTHBJK1Rjb1Jzb0VKa3Vvc1VURm01V3FQcTRBeFJKb3RlTzZBZmhxZEJaegorSGM3V041Y0dyVjdJNGFsMW8wQ0F3RUFBYU5GTUVNd0RnWURWUjBQQVFIL0JBUURBZ0trTUJJR0ExVWRFd0VCCi93UUlNQVlCQWY4Q0FRQXdIUVlEVlIwT0JCWUVGQmE2elJ6R0tKUU54dFNDL2d4YVBYUXZaZXp3TUEwR0NTcUcKU0liM0RRRUJDd1VBQTRJQkFRQXlHb3hNR0ZZbDJlT1cyTWxZTTBMc29DeEtzRXByb3N4dVVpOExBd2tDR2UreApQN1lLU2tVZVcweVRiSGNib3UvUXY0aVFGdUNWUVVXSWtKZkgvR3lTcEpjRWNlc2xVZE1GalFweXN1cndJamdEClJuQURqUnRBUkp5OTRNVnZ0Tm40Y0J3VGpuRjgyeG5Rc0EzNFFuVWZ6a2tNMkNoQ1ZuWTVoR3k0R0s5Y3M2WDUKdjEza3paaUFWSXg4Q0tPV0lNNmZLRVRMV09zcTgva011dDdDWHcyWWhlVzI1NFpMcEtZVWNkRzdBTVQySHE2dgo2TmlNa05WQUVvemg5WkxQcm5BeXhYY01EU1IrOW56cDJtMy9aMVdrWlc2TUljNVJYLzEvYWI2Q0JHbTg3YXJGClZJblJzUHpjeW1iUUZQSCsrNm14K1REcFBSZW5FK2FLa1hyZ05yVU8KLS0tLS1FTkQgQ0VSVElGSUNBVEUtLS0tLQo=
    server: https://127.0.0.1:6443
  name: test-test
contexts:
- context:
    cluster: test-test
    user: kubernetes-admin
  name: kubernetes-admin@test-test
current-context: kubernetes-admin@test-test
kind: Config
preferences: {}
users:
- name: kubernetes-admin
  user:
    client-certificate-data: LS0tLS1CRUdJTiBDRVJUSUZJQ0FURS0tLS0tCk1JSURJVENDQWdtZ0F3SUJBZ0lJRUxFRkd2aExNcWt3RFFZSktvWklodmNOQVFFTEJRQXdGVEVUTUJFR0ExVUUKQXhNS2EzVmlaWEp1WlhSbGN6QWVGdzB5TXpFeU1EY3dPVEU1TkRCYUZ3MHlOVEF4TXpBd01qQTVNakphTURReApGekFWQmdOVkJBb1REbk41YzNSbGJUcHRZWE4wWlhKek1Sa3dGd1lEVlFRREV4QnJkV0psY201bGRHVnpMV0ZrCmJXbHVNSUlCSWpBTkJna3Foa2lHOXcwQkFRRUZBQU9DQVE4QU1JSUJDZ0tDQVFFQTBGK3V3SXgwMlVpSXE4TG8KV2F0eVU0LzVpbWxlcEhjN0dTemJIZzhkTUp5UU1NV2phTkFLQ2g2K2VUY0czbmJ3aUtIajhUalU2YzdlVU1WWApsR2dNMDNWa291M09ZTWczbjI3dSt1amV4ZlVmVVI5Q3VhMURTN2NLRytMenplMitWTFpKeElmUnpDNXc1MXBOCjZjc2wrcmRHeW9Wb1phYmVUUis3bDhEd2ZrdzRkME85TUFjUVlpSEZWSDNRS052ekFwVnhmY0NjTjdPbE14TkYKc2dLOXZ4aEpkWk8zTHFkOElVNU4ySnZENEFxaG8vbEtGTWNCK3RBMjRqb1prTy9ydklVOXJBMEVyRDd6V1lTWApLTzU0Wm14NnUxVURqaTRXaFl6aU51TmkrU3BvelY2cllsYnhnUTJYNXVhVHVlSlJYTFdTNjkyR2JEUzI5OGJoCkE1NTJNUUlEQVFBQm8xWXdWREFPQmdOVkhROEJBZjhFQkFNQ0JhQXdFd1lEVlIwbEJBd3dDZ1lJS3dZQkJRVUgKQXdJd0RBWURWUjBUQVFIL0JBSXdBREFmQmdOVkhTTUVHREFXZ0JRV3VzMGN4aWlVRGNiVWd2NE1XajEwTDJYcwo4REFOQmdrcWhraUc5dzBCQVFzRkFBT0NBUUVBbjk1RVpucFczM3Nra2ZwWk1PRnQyQ1NGZkF5Qm9SL1VMOEdDClpKZG5SdHlBcTV3Mlo3cExKZy9DSVZtc1hZUEpDUlExSVlTS0JJU29ndGV0ZDFENXhQR2hOYzA3cEhyWUhoVGgKNFJteUpKOWdIWjRUYVo5STIybFRqWk5MWm9zNXIrQ2RHelhvMGJGOTh0dDJSRG8xbGVrbWJjSitKcHo4ZnJiNgpIdlVCWUZuL0FsUWgzUnpsWEZkbEVPekNMQlN4TmplRzRWbnpqZ0NNc01ZdmdBbEEwMUlEK1YzYS90bC9qTHJlCnNheGRVNTZlSTdaY0FSaVUzZVJWOC9zMWFJd2JmNk5Tam1zSElzeDdxcXFiVEczS0tDVmJGUzkrNWlyMEoxVk0KaytBbndnTWlkb08wTmxGUEErTmVZNzFFcHYxdGZwOWtIMWVUc3dKTUtBbHJOa2Q0aGc9PQotLS0tLUVORCBDRVJUSUZJQ0FURS0tLS0tCg==
    client-key-data: LS0tLS1CRUdJTiBSU0EgUFJJVkFURSBLRVktLS0tLQpNSUlFb3dJQkFBS0NBUUVBMEYrdXdJeDAyVWlJcThMb1dhdHlVNC81aW1sZXBIYzdHU3piSGc4ZE1KeVFNTVdqCmFOQUtDaDYrZVRjRzNuYndpS0hqOFRqVTZjN2VVTVZYbEdnTTAzVmtvdTNPWU1nM24yN3UrdWpleGZVZlVSOUMKdWExRFM3Y0tHK0x6emUyK1ZMWkp4SWZSekM1dzUxcE42Y3NsK3JkR3lvVm9aYWJlVFIrN2w4RHdma3c0ZDBPOQpNQWNRWWlIRlZIM1FLTnZ6QXBWeGZjQ2NON09sTXhORnNnSzl2eGhKZFpPM0xxZDhJVTVOMkp2RDRBcWhvL2xLCkZNY0IrdEEyNGpvWmtPL3J2SVU5ckEwRXJEN3pXWVNYS081NFpteDZ1MVVEamk0V2hZemlOdU5pK1Nwb3pWNnIKWWxieGdRMlg1dWFUdWVKUlhMV1M2OTJHYkRTMjk4YmhBNTUyTVFJREFRQUJBb0lCQVFDVEU1WlRUbENEdFpEUwpPNmFvOUR5a0FyR09Jc1dzcklQSVIwTDZPb3pON1JSUmVJN1l3azd6eWJPRDkzVWZ2VEFXSUw2MVd2bmRkaWl4Ck5qbVZCTVJZMVRtTlR2RW1tdXUzMnlOUGN1TWJNdU5CN1NDNTBqUDMwMkNOUW1uMzVtRTdoZGNYb3c1UVlrOUsKM1JDMWZyQjJBTHMwNDJsR3BydXVFRUhtNFVaZXZjUHBvU3dZQXVRekZ0enJuNDhid0hTZlNGcS9KZVh6N2FOUgpCZWxRSmR3S0xCbk1NMlA4VmtONGtLNkZtc25pVFJtTElBY2QrWUxyWStNcDJuRmxYNDNxT2h3TTliTTlJcUJwClh4anJFd0JqRVNudjdHdUZYNGRodFBSd0hHRHJXWm5WWm9GVVBXV1Nkem1vQzlxMUc4alRCRlF6WmFDT2k3engKY3hucXZWeXBBb0dCQU9jdVp5OGtuRjBVSzFYOGVlVkFhK00zaWRtSy92V0RETFFydU12S1VOMDBrZFZPaTcvTwpXTDl1djJ1UkhBUFh1T2dEa0J4U25FcmVVMU9UK1c1dlVidlVZU0dhZkozYkRGOE96dHU2UkYvaXlmRkMzTi9MCnhlZUpsY3p4RHNqSkhYM1M0TTBnOGNqY2EwaUNXam9iNnkxZTA0dHdGM0xZdEpRWDZMSm1KK1ViQW9HQkFPYSsKZFBJTlBOVDhVOSs2clF5U0ZiZytjRVZxRHdZalU2MnZhSllqM2ZORXdyWERsaUNTK2lTSlJiZFBjeTNtNjZvbQozRXlqb0ROdjU5UEtEZW5FcGtneit6WGxiNWdMYXZtY2tDZEszcXhsNnpwNFB2YXdzUmtCdUFhZm1mVFpvRGhYCk8wYmtQV2I3R0htbjRUZlI3YmpIZWI5ZEZRYjlrU1BhWGQ3Qi9pS2pBb0dBSEFQdGtUTDRsL2NId1dYVlI4amsKeWlaQzJGQVYwWjdOL1UrSEYzc3ZEWDkvWk1BZUEySjRNc3F5KzlBYit3TTdiekp2Vmw5VWZXWXY1dUw1eVQ1SQpRMkRiWEgwaU9PY0F1c3hLbVNvYmV4czZxYmdXbURCVGpWbUpBOHI2cGE1cG1vUGhwam9sMHRlVFVMZ3JRdnQ3CkpvWmxVSEtIQk8zcUJFQlpmTFVRaEowQ2dZQkh6TklGRTl0dkJ3bHVYOTlEUHgzbEZBREppTVFlQzlZWkFMRVIKcngxOGVsUUFUVmtrejdkb3NSSnhoUlo1SFJjTi9rT2swWEdqTDlvNmkvQWlZdCsvTGZXb2dybGozWUd2SkdteQo0RmhEMnY4RVZiQjZBT2RLdWI4eXlHMFd4TFZYY3NWdVBNMWlneFhOblZDMmx1dGJDUzg0UGRXeU5DcjZ0aE5wCm9vSGE4d0tCZ0UrSWY3STJ2UGxoRWtFaFkvc2Q1NzNCSkdxa2VGcnEvbmw1bW4rL0J3YWI4RXNsY1V1blFnQmQKcm93aEI0ODJETitJbDdiNVhxWWYvNnk5YnVoZkhsakpoRFJMN1BGM1BsUklQQmdYdHRQbHB3RVd1NG13NVI3MApHRVZ0SE95TFhwS0JQdStnSkNVTDBaT1FJMkN6Ym1IbWt1ejA5RWpHeXh5YmVLbDZXTFo0Ci0tLS0tRU5EIFJTQSBQUklWQVRFIEtFWS0tLS0tCg==
    """


def write_bad_temp_kubeconfig(
        remove_key=None
):
    """Generate kubeconfig in tmp
    :return: return path to temporary kubeconfig file
    """
    kubeconfig_data = generate_bad_config(remove_key=remove_key)
    temp_fd, temp_path = tempfile.mkstemp()
    with os.fdopen(temp_fd, 'w') as temp_file:
        temp_file.write(kubeconfig_data)
    return temp_path


def generate_bad_config(
        remove_key=None
):
    """Generate an invalid kube config for unit test by removing a specified key.

    :param remove_key: The key to remove from the kubeconfig data structure. This could be
                       'clusters', 'users', 'contexts', or any other top-level key in the
                       kubeconfig structure.
    :return: A string representation of the modified kube config.
    """
    config = """
apiVersion: v1
clusters:
- cluster:
    certificate-authority-data: LS0tLS1CRUdJTiBDRVJUSUZJQ0FURS0tLS0tCk1JSUM2akNDQWRLZ0F3SUJBZ0lCQURBTkJna3Foa2lHOXcwQkFRc0ZBREFWTVJNd0VRWURWUVFERXdwcmRXSmwKY201bGRHVnpNQjRYRFRJek1USXdOekE1TVRrME1Gb1hEVE16TVRJd05EQTVNalEwTUZvd0ZURVRNQkVHQTFVRQpBeE1LYTNWaVpYSnVaWFJsY3pDQ0FTSXdEUVlKS29aSWh2Y05BUUVCQlFBRGdnRVBBRENDQVFvQ2dnRUJBTjUzCmQwcjJrVGI5YmRKSjlRWmp2d2FJVEdVd3JRWUtFc2p1amdiZXRjZDZxSGlZUjFNdTNjSXVORWh1VnB3MkRrV1oKZ3dtMHpiV1JaNXFxbVVCODBiTWpHbFk0YnBkRExUcEl1OCtkRmlwOHo0VjMyY3VqZXRadEMyd2gyYStycnZsagpDUWZDTnJvU2NUYnhiNGRlVGt0bGtONUs4ZEMwWkg2NlpKWklNcmd3YytwMkJZTjNFeGxMSmwwZ21HZkNTMnB1CjFOcFgzUmJKbFZVQ3gwb2VTekI3ZEtqb0wzS0J4eUZRRTBYSllmeEhZd1Z1U3VTd3BUU1BwbWcwTzlHc0tQV0kKUnZ2ZStaWHdlNGVHN1BMYlhtZWhXTHBJK1Rjb1Jzb0VKa3Vvc1VURm01V3FQcTRBeFJKb3RlTzZBZmhxZEJaegorSGM3V041Y0dyVjdJNGFsMW8wQ0F3RUFBYU5GTUVNd0RnWURWUjBQQVFIL0JBUURBZ0trTUJJR0ExVWRFd0VCCi93UUlNQVlCQWY4Q0FRQXdIUVlEVlIwT0JCWUVGQmE2elJ6R0tKUU54dFNDL2d4YVBYUXZaZXp3TUEwR0NTcUcKU0liM0RRRUJDd1VBQTRJQkFRQXlHb3hNR0ZZbDJlT1cyTWxZTTBMc29DeEtzRXByb3N4dVVpOExBd2tDR2UreApQN1lLU2tVZVcweVRiSGNib3UvUXY0aVFGdUNWUVVXSWtKZkgvR3lTcEpjRWNlc2xVZE1GalFweXN1cndJamdEClJuQURqUnRBUkp5OTRNVnZ0Tm40Y0J3VGpuRjgyeG5Rc0EzNFFuVWZ6a2tNMkNoQ1ZuWTVoR3k0R0s5Y3M2WDUKdjEza3paaUFWSXg4Q0tPV0lNNmZLRVRMV09zcTgva011dDdDWHcyWWhlVzI1NFpMcEtZVWNkRzdBTVQySHE2dgo2TmlNa05WQUVvemg5WkxQcm5BeXhYY01EU1IrOW56cDJtMy9aMVdrWlc2TUljNVJYLzEvYWI2Q0JHbTg3YXJGClZJblJzUHpjeW1iUUZQSCsrNm14K1REcFBSZW5FK2FLa1hyZ05yVU8KLS0tLS1FTkQgQ0VSVElGSUNBVEUtLS0tLQo=
    server: https://127.0.0.1:6443
  name: test-test
contexts:
- context:
    cluster: test-test
    user: kubernetes-admin
  name: kubernetes-admin@vf-test
current-context: kubernetes-admin@test-test
kind: Config
preferences: {}
users:
- name: kubernetes-admin
  user:
    client-certificate-data: LS0tLS1CRUdJTiBDRVJUSUZJQ0FURS0tLS0tCk1JSURJVENDQWdtZ0F3SUJBZ0lJRUxFRkd2aExNcWt3RFFZSktvWklodmNOQVFFTEJRQXdGVEVUTUJFR0ExVUUKQXhNS2EzVmlaWEp1WlhSbGN6QWVGdzB5TXpFeU1EY3dPVEU1TkRCYUZ3MHlOVEF4TXpBd01qQTVNakphTURReApGekFWQmdOVkJBb1REbk41YzNSbGJUcHRZWE4wWlhKek1Sa3dGd1lEVlFRREV4QnJkV0psY201bGRHVnpMV0ZrCmJXbHVNSUlCSWpBTkJna3Foa2lHOXcwQkFRRUZBQU9DQVE4QU1JSUJDZ0tDQVFFQTBGK3V3SXgwMlVpSXE4TG8KV2F0eVU0LzVpbWxlcEhjN0dTemJIZzhkTUp5UU1NV2phTkFLQ2g2K2VUY0czbmJ3aUtIajhUalU2YzdlVU1WWApsR2dNMDNWa291M09ZTWczbjI3dSt1amV4ZlVmVVI5Q3VhMURTN2NLRytMenplMitWTFpKeElmUnpDNXc1MXBOCjZjc2wrcmRHeW9Wb1phYmVUUis3bDhEd2ZrdzRkME85TUFjUVlpSEZWSDNRS052ekFwVnhmY0NjTjdPbE14TkYKc2dLOXZ4aEpkWk8zTHFkOElVNU4ySnZENEFxaG8vbEtGTWNCK3RBMjRqb1prTy9ydklVOXJBMEVyRDd6V1lTWApLTzU0Wm14NnUxVURqaTRXaFl6aU51TmkrU3BvelY2cllsYnhnUTJYNXVhVHVlSlJYTFdTNjkyR2JEUzI5OGJoCkE1NTJNUUlEQVFBQm8xWXdWREFPQmdOVkhROEJBZjhFQkFNQ0JhQXdFd1lEVlIwbEJBd3dDZ1lJS3dZQkJRVUgKQXdJd0RBWURWUjBUQVFIL0JBSXdBREFmQmdOVkhTTUVHREFXZ0JRV3VzMGN4aWlVRGNiVWd2NE1XajEwTDJYcwo4REFOQmdrcWhraUc5dzBCQVFzRkFBT0NBUUVBbjk1RVpucFczM3Nra2ZwWk1PRnQyQ1NGZkF5Qm9SL1VMOEdDClpKZG5SdHlBcTV3Mlo3cExKZy9DSVZtc1hZUEpDUlExSVlTS0JJU29ndGV0ZDFENXhQR2hOYzA3cEhyWUhoVGgKNFJteUpKOWdIWjRUYVo5STIybFRqWk5MWm9zNXIrQ2RHelhvMGJGOTh0dDJSRG8xbGVrbWJjSitKcHo4ZnJiNgpIdlVCWUZuL0FsUWgzUnpsWEZkbEVPekNMQlN4TmplRzRWbnpqZ0NNc01ZdmdBbEEwMUlEK1YzYS90bC9qTHJlCnNheGRVNTZlSTdaY0FSaVUzZVJWOC9zMWFJd2JmNk5Tam1zSElzeDdxcXFiVEczS0tDVmJGUzkrNWlyMEoxVk0KaytBbndnTWlkb08wTmxGUEErTmVZNzFFcHYxdGZwOWtIMWVUc3dKTUtBbHJOa2Q0aGc9PQotLS0tLUVORCBDRVJUSUZJQ0FURS0tLS0tCg==
    client-key-data: LS0tLS1CRUdJTiBSU0EgUFJJVkFURSBLRVktLS0tLQpNSUlFb3dJQkFBS0NBUUVBMEYrdXdJeDAyVWlJcThMb1dhdHlVNC81aW1sZXBIYzdHU3piSGc4ZE1KeVFNTVdqCmFOQUtDaDYrZVRjRzNuYndpS0hqOFRqVTZjN2VVTVZYbEdnTTAzVmtvdTNPWU1nM24yN3UrdWpleGZVZlVSOUMKdWExRFM3Y0tHK0x6emUyK1ZMWkp4SWZSekM1dzUxcE42Y3NsK3JkR3lvVm9aYWJlVFIrN2w4RHdma3c0ZDBPOQpNQWNRWWlIRlZIM1FLTnZ6QXBWeGZjQ2NON09sTXhORnNnSzl2eGhKZFpPM0xxZDhJVTVOMkp2RDRBcWhvL2xLCkZNY0IrdEEyNGpvWmtPL3J2SVU5ckEwRXJEN3pXWVNYS081NFpteDZ1MVVEamk0V2hZemlOdU5pK1Nwb3pWNnIKWWxieGdRMlg1dWFUdWVKUlhMV1M2OTJHYkRTMjk4YmhBNTUyTVFJREFRQUJBb0lCQVFDVEU1WlRUbENEdFpEUwpPNmFvOUR5a0FyR09Jc1dzcklQSVIwTDZPb3pON1JSUmVJN1l3azd6eWJPRDkzVWZ2VEFXSUw2MVd2bmRkaWl4Ck5qbVZCTVJZMVRtTlR2RW1tdXUzMnlOUGN1TWJNdU5CN1NDNTBqUDMwMkNOUW1uMzVtRTdoZGNYb3c1UVlrOUsKM1JDMWZyQjJBTHMwNDJsR3BydXVFRUhtNFVaZXZjUHBvU3dZQXVRekZ0enJuNDhid0hTZlNGcS9KZVh6N2FOUgpCZWxRSmR3S0xCbk1NMlA4VmtONGtLNkZtc25pVFJtTElBY2QrWUxyWStNcDJuRmxYNDNxT2h3TTliTTlJcUJwClh4anJFd0JqRVNudjdHdUZYNGRodFBSd0hHRHJXWm5WWm9GVVBXV1Nkem1vQzlxMUc4alRCRlF6WmFDT2k3engKY3hucXZWeXBBb0dCQU9jdVp5OGtuRjBVSzFYOGVlVkFhK00zaWRtSy92V0RETFFydU12S1VOMDBrZFZPaTcvTwpXTDl1djJ1UkhBUFh1T2dEa0J4U25FcmVVMU9UK1c1dlVidlVZU0dhZkozYkRGOE96dHU2UkYvaXlmRkMzTi9MCnhlZUpsY3p4RHNqSkhYM1M0TTBnOGNqY2EwaUNXam9iNnkxZTA0dHdGM0xZdEpRWDZMSm1KK1ViQW9HQkFPYSsKZFBJTlBOVDhVOSs2clF5U0ZiZytjRVZxRHdZalU2MnZhSllqM2ZORXdyWERsaUNTK2lTSlJiZFBjeTNtNjZvbQozRXlqb0ROdjU5UEtEZW5FcGtneit6WGxiNWdMYXZtY2tDZEszcXhsNnpwNFB2YXdzUmtCdUFhZm1mVFpvRGhYCk8wYmtQV2I3R0htbjRUZlI3YmpIZWI5ZEZRYjlrU1BhWGQ3Qi9pS2pBb0dBSEFQdGtUTDRsL2NId1dYVlI4amsKeWlaQzJGQVYwWjdOL1UrSEYzc3ZEWDkvWk1BZUEySjRNc3F5KzlBYit3TTdiekp2Vmw5VWZXWXY1dUw1eVQ1SQpRMkRiWEgwaU9PY0F1c3hLbVNvYmV4czZxYmdXbURCVGpWbUpBOHI2cGE1cG1vUGhwam9sMHRlVFVMZ3JRdnQ3CkpvWmxVSEtIQk8zcUJFQlpmTFVRaEowQ2dZQkh6TklGRTl0dkJ3bHVYOTlEUHgzbEZBREppTVFlQzlZWkFMRVIKcngxOGVsUUFUVmtrejdkb3NSSnhoUlo1SFJjTi9rT2swWEdqTDlvNmkvQWlZdCsvTGZXb2dybGozWUd2SkdteQo0RmhEMnY4RVZiQjZBT2RLdWI4eXlHMFd4TFZYY3NWdVBNMWlneFhOblZDMmx1dGJDUzg0UGRXeU5DcjZ0aE5wCm9vSGE4d0tCZ0UrSWY3STJ2UGxoRWtFaFkvc2Q1NzNCSkdxa2VGcnEvbmw1bW4rL0J3YWI4RXNsY1V1blFnQmQKcm93aEI0ODJETitJbDdiNVhxWWYvNnk5YnVoZkhsakpoRFJMN1BGM1BsUklQQmdYdHRQbHB3RVd1NG13NVI3MApHRVZ0SE95TFhwS0JQdStnSkNVTDBaT1FJMkN6Ym1IbWt1ejA5RWpHeXh5YmVLbDZXTFo0Ci0tLS0tRU5EIFJTQSBQUklWQVRFIEtFWS0tLS0tCg==
    """

    config_dict = yaml.safe_load(config)
    if remove_key and remove_key in config_dict:
        del config_dict[remove_key]

    modified_config = yaml.dump(config_dict, default_flow_style=False)
    return modified_config


def sample_control_node():
    return """
    {
    "apiVersion": "v1",
    "kind": "Node",
    "metadata": {
        "annotations": {
            "cluster.x-k8s.io/cluster-name": "vf-test",
            "cluster.x-k8s.io/cluster-namespace": "vf-test",
            "cluster.x-k8s.io/labels-from-machine": "node.cluster.x-k8s.io/esxi-host",
            "cluster.x-k8s.io/machine": "vf-test-hcpdj-8tctj",
            "cluster.x-k8s.io/owner-kind": "KubeadmControlPlane",
            "cluster.x-k8s.io/owner-name": "vf-test-hcpdj",
            "kubeadm.alpha.kubernetes.io/cri-socket": "unix:///var/run/containerd/containerd.sock",
            "node.alpha.kubernetes.io/ttl": "0",
            "tcacluster.telco.vmware.com/backup-labels": "",
            "volumes.kubernetes.io/controller-managed-attach-detach": "true"
        },
        "creationTimestamp": "2023-12-07T09:25:30Z",
        "labels": {
            "beta.kubernetes.io/arch": "amd64",
            "beta.kubernetes.io/instance-type": "vsphere-vm.cpu-8.mem-16gb.os-photon",
            "beta.kubernetes.io/os": "linux",
            "image-type": "ova",
            "kubernetes.io/arch": "amd64",
            "kubernetes.io/hostname": "vf-test-hcpdj-8tctj",
            "kubernetes.io/os": "linux",
            "node-role.kubernetes.io/control-plane": "",
            "node.cluster.x-k8s.io/esxi-host": "10.252.80.109",
            "node.kubernetes.io/exclude-from-external-load-balancers": "",
            "node.kubernetes.io/instance-type": "vsphere-vm.cpu-8.mem-16gb.os-photon",
            "os-name": "photon",
            "os-type": "linux"
        },
        "name": "vf-test-hcpdj-8tctj",
        "resourceVersion": "28765528",
        "uid": "caffa104-be61-420a-a591-3a06b3ff2219"
    },
    "spec": {
        "podCIDR": "100.96.0.0/24",
        "podCIDRs": [
            "100.96.0.0/24"
        ],
        "providerID": "vsphere://4236b429-6bb9-38ae-35ab-0abfe1e41dcc",
        "taints": [
            {
                "effect": "NoSchedule",
                "key": "node-role.kubernetes.io/control-plane"
            }
        ]
    },
    "status": {
        "addresses": [
            {
                "address": "vf-test-hcpdj-8tctj",
                "type": "Hostname"
            },
            {
                "address": "198.19.57.114",
                "type": "InternalIP"
            },
            {
                "address": "198.19.57.114",
                "type": "ExternalIP"
            }
        ],
        "allocatable": {
            "cpu": "16",
            "ephemeral-storage": "37867920936",
            "hugepages-1Gi": "0",
            "hugepages-2Mi": "0",
            "memory": "65851056Ki",
            "pods": "110"
        },
        "capacity": {
            "cpu": "16",
            "ephemeral-storage": "41089324Ki",
            "hugepages-1Gi": "0",
            "hugepages-2Mi": "0",
            "memory": "65953456Ki",
            "pods": "110"
        },
        "conditions": [
            {
                "lastHeartbeatTime": "2024-03-02T01:42:26Z",
                "lastTransitionTime": "2024-01-29T14:30:01Z",
                "message": "kubelet has sufficient memory available",
                "reason": "KubeletHasSufficientMemory",
                "status": "False",
                "type": "MemoryPressure"
            },
            {
                "lastHeartbeatTime": "2024-03-02T01:42:26Z",
                "lastTransitionTime": "2024-01-29T14:30:01Z",
                "message": "kubelet has no disk pressure",
                "reason": "KubeletHasNoDiskPressure",
                "status": "False",
                "type": "DiskPressure"
            },
            {
                "lastHeartbeatTime": "2024-03-02T01:42:26Z",
                "lastTransitionTime": "2024-01-29T14:30:01Z",
                "message": "kubelet has sufficient PID available",
                "reason": "KubeletHasSufficientPID",
                "status": "False",
                "type": "PIDPressure"
            },
            {
                "lastHeartbeatTime": "2024-03-02T01:42:26Z",
                "lastTransitionTime": "2024-01-31T01:50:25Z",
                "message": "kubelet is posting ready status",
                "reason": "KubeletReady",
                "status": "True",
                "type": "Ready"
            }
        ],
        "daemonEndpoints": {
            "kubeletEndpoint": {
                "Port": 10250
            }
        },
        "images": [
            {
                "names": [
                    "projects.registry.vmware.com/tkg/antreainterworking/interworking-debian@sha256:cd14f52b5ec4fc77863e4e64daa961890a964d7b584b6f4eb6ebac43b903e69f"
                ],
                "sizeBytes": 491038937
            },
            {
                "names": [
                    "projects.registry.vmware.com/tkg/antrea-advanced-debian@sha256:c4ad5f9e8d846daf6fa80f79ed61c88aa60bc03a49e8a6b4b1fad21841ec5275"
                ],
                "sizeBytes": 271957682
            },
            {
                "names": [
                    "projects.registry.vmware.com/tkg/kapp-controller@sha256:296be94e61f4c7150e8a1eeb6fb0882cb4dd9d341b74bd2ac4538a28093884a4"
                ],
                "sizeBytes": 166547996
            },
            {
                "names": [
                    "projects.registry.vmware.com/tkg/etcd:v3.5.6_vmware.20"
                ],
                "sizeBytes": 142673295
            },
            {
                "names": [
                    "projects.registry.vmware.com/tkg/kube-apiserver:v1.26.8_vmware.1"
                ],
                "sizeBytes": 137331248
            },
            {
                "names": [
                    "projects.registry.vmware.com/tkg/kube-controller-manager:v1.26.8_vmware.1"
                ],
                "sizeBytes": 126394534
            },
            {
                "names": [
                    "projects.registry.vmware.com/tkg/csi/vsphere-block-csi-driver@sha256:c3dfbbd85dd5cac17bf694c1acdbde135c5c9aa4433e57cfb6c2137e494305bb"
                ],
                "sizeBytes": 107865128
            },
            {
                "names": [
                    "projects.registry.vmware.com/tkg/kube-proxy:v1.26.8_vmware.1"
                ],
                "sizeBytes": 65403925
            },
            {
                "names": [
                    "projects.registry.vmware.com/tkg/kube-scheduler:v1.26.8_vmware.1"
                ],
                "sizeBytes": 58929829
            },
            {
                "names": [
                    "projects.registry.vmware.com/tkg/csi/volume-metadata-syncer@sha256:2a61a84059113621c057144151f71f2e5c78d36902434f69639e006cc9c11f7b"
                ],
                "sizeBytes": 56681237
            },
            {
                "names": [
                    "vmwaresaas.jfrog.io/registry/nodeconfig-daemon@sha256:a63af1da505ede9f3ff03c09e0edf36b831dfc14fcd4be49d02795ec54aefc95"
                ],
                "sizeBytes": 54877278
            },
            {
                "names": [
                    "projects.registry.vmware.com/tkg/coredns:v1.9.3_vmware.16"
                ],
                "sizeBytes": 49870816
            },
            {
                "names": [
                    "projects.registry.vmware.com/tkg/whereabouts@sha256:54e87e66b501b86116ee6296bd4ba8040d922d0b3b7718192f3df393ddae1039"
                ],
                "sizeBytes": 43822425
            },
            {
                "names": [
                    "projects.registry.vmware.com/tkg/multus-cni@sha256:d378d81a80fc7910f7d452760329a2f11868876a82cc393874a85474dafa7a1d"
                ],
                "sizeBytes": 41755402
            },
            {
                "names": [
                    "projects.registry.vmware.com/tkg/csi/csi-provisioner@sha256:38e9f3488145579e303652e5e590cf3f7b92a2599d23c29402800b6abab892cb"
                ],
                "sizeBytes": 30638100
            },
            {
                "names": [
                    "projects.registry.vmware.com/tkg/csi/csi-snapshotter@sha256:90642e840abf41d4a657c47a86ec0f8228e9ad559b1cca7f141a06913f067414"
                ],
                "sizeBytes": 29910074
            },
            {
                "names": [
                    "projects.registry.vmware.com/tkg/csi/kubernetes-csi_external-resizer@sha256:786a268f3bbc8909cb6f5a1444b0906422e8747cbab23f7c5745ea959c6228c7"
                ],
                "sizeBytes": 29784353
            },
            {
                "names": [
                    "projects.registry.vmware.com/tkg/csi/csi-attacher@sha256:27ff61fd52e8cbb43d48c9ee7ebb762cbfa55c0d4955a90ab7a2e9b35fa98c70"
                ],
                "sizeBytes": 29631708
            },
            {
                "names": [
                    "projects.registry.vmware.com/tkg/tanzu_core/capabilities/capabilities-controller-manager@sha256:02bbb904e4aa92cbf3b446cf203e6673790b087a9184824e78749b7216a8645d"
                ],
                "sizeBytes": 24630852
            },
            {
                "names": [
                    "projects.registry.vmware.com/tkg/csi/csi-node-driver-registrar@sha256:e9cd55b95d477ed887cb3266cfcd0868c8e487d4eb2f1e34a8f7183296c39776"
                ],
                "sizeBytes": 21862235
            },
            {
                "names": [
                    "docker.io/aquasec/kube-bench@sha256:959b65e754aca8f15710bff618c95c625f5d5c2d5845b04958fcf784ebfe4aea",
                    "docker.io/aquasec/kube-bench:v0.6.14"
                ],
                "sizeBytes": 21599141
            },
            {
                "names": [
                    "projects.registry.vmware.com/tkg/csi/csi-livenessprobe@sha256:b8875efc3066ec192d9e6d933b9da772fcb415e5b0d069a34e4c3d228123f9f0"
                ],
                "sizeBytes": 21364839
            },
            {
                "names": [
                    "projects.registry.vmware.com/tkg/ccm/manager@sha256:b1eaff43feffa899a6b1b559170af310050b530f94287fc91521752416fa7f7a"
                ],
                "sizeBytes": 20335501
            },
            {
                "names": [
                    "projects.registry.vmware.com/tkg/kube-vip@sha256:787bf383d0c51ff1fb75d4bf02d16d53cf49ba1d4eaad9a73bcb7be01651551b",
                    "projects.registry.vmware.com/tkg/kube-vip:v0.5.12_vmware.1"
                ],
                "sizeBytes": 15202484
            },
            {
                "names": [
                    "projects.registry.vmware.com/tkg/pause:3.9"
                ],
                "sizeBytes": 739186
            }
        ],
        "nodeInfo": {
            "architecture": "amd64",
            "bootID": "c41ee4d0-a604-4a68-9caf-f8b14e17a8b4",
            "containerRuntimeVersion": "containerd://1.6.18-1-gdbc99e5b1",
            "kernelVersion": "4.19.290-3.ph3",
            "kubeProxyVersion": "v1.26.8+vmware.1",
            "kubeletVersion": "v1.26.8+vmware.1",
            "machineID": "e4b4b1484ba147faa27abbc0352d1059",
            "operatingSystem": "linux",
            "osImage": "VMware Photon OS/Linux",
            "systemUUID": "29b43642-b96b-ae38-35ab-0abfe1e41dcc"
        }
    }
}"""


def sample_worker_node():
    return """
{
    "apiVersion": "v1",
    "kind": "Node",
    "metadata": {
        "annotations": {
            "node.alpha.kubernetes.io/ttl": "0",
            "volumes.kubernetes.io/controller-managed-attach-detach": "true"
        },
        "creationTimestamp": "2024-02-06T17:51:37Z",
        "labels": {
            "beta.kubernetes.io/arch": "amd64",
            "beta.kubernetes.io/instance-type": "vsphere-vm.cpu-32.mem-64gb.os-photon",
            "beta.kubernetes.io/os": "linux",
            "image-type": "ova",
            "kubernetes.io/arch": "amd64",
            "kubernetes.io/hostname": "vf-test-np1-h5mtj-9cf8fdcf6xcfln5-k6mdx",
            "kubernetes.io/os": "linux",
            "node.kubernetes.io/instance-type": "vsphere-vm.cpu-32.mem-64gb.os-photon",
            "os-name": "photon",
            "os-type": "linux"
        },
        "name": "vf-test-np1-h5mtj-9cf8fdcf6xcfln5-k6mdx",
        "resourceVersion": "28766512",
        "uid": "18f340b2-0487-4dde-86f6-e567702a5dfd"
    },
    "spec": {
        "podCIDR": "100.96.16.0/22",
        "podCIDRs": [
            "100.96.16.0/22"
        ],
        "providerID": "vsphere://4236d5ce-6fe8-725c-2429-954c402d660c"
    },
    "status": {
        "addresses": [
            {
                "address": "vf-test-np1-h5mtj-9cf8fdcf6xcfln5-k6mdx",
                "type": "Hostname"
            },
            {
                "address": "198.19.57.189",
                "type": "InternalIP"
            },
            {
                "address": "198.19.57.189",
                "type": "ExternalIP"
            }
        ],
        "allocatable": {
            "cpu": "30",
            "ephemeral-storage": "66400406214",
            "hugepages-1Gi": "0",
            "hugepages-2Mi": "0",
            "memory": "61720948Ki",
            "pods": "10242"
        },
        "capacity": {
            "cpu": "32",
            "ephemeral-storage": "72049052Ki",
            "hugepages-1Gi": "0",
            "hugepages-2Mi": "0",
            "memory": "66017652Ki",
            "pods": "10242"
        },
        "conditions": [
            {
                "lastHeartbeatTime": "2024-03-02T01:46:41Z",
                "lastTransitionTime": "2024-02-14T01:35:45Z",
                "message": "kubelet has sufficient memory available",
                "reason": "KubeletHasSufficientMemory",
                "status": "False",
                "type": "MemoryPressure"
            },
            {
                "lastHeartbeatTime": "2024-03-02T01:46:41Z",
                "lastTransitionTime": "2024-02-14T01:35:45Z",
                "message": "kubelet has no disk pressure",
                "reason": "KubeletHasNoDiskPressure",
                "status": "False",
                "type": "DiskPressure"
            },
            {
                "lastHeartbeatTime": "2024-03-02T01:46:41Z",
                "lastTransitionTime": "2024-02-14T01:35:45Z",
                "message": "kubelet has sufficient PID available",
                "reason": "KubeletHasSufficientPID",
                "status": "False",
                "type": "PIDPressure"
            },
            {
                "lastHeartbeatTime": "2024-03-02T01:46:41Z",
                "lastTransitionTime": "2024-02-14T01:35:45Z",
                "message": "kubelet is posting ready status",
                "reason": "KubeletReady",
                "status": "True",
                "type": "Ready"
            }
        ],
        "daemonEndpoints": {
            "kubeletEndpoint": {
                "Port": 10250
            }
        },
        "images": [
            {
                "names": [
                    "docker.io/spyroot/pktgen_toolbox_generic@sha256:b03ad12b0d9eee1354f97d5447a87cc1e387260e5c518c4b8be3b0d672840fa9",
                    "docker.io/spyroot/pktgen_toolbox_generic:latest"
                ],
                "sizeBytes": 3733354508
            },
            {
                "names": [
                    "docker.io/voereir/touchstone-server-ubuntu@sha256:61b22d2de38e1f02ee31e034875044119a74bac01b2ba319ae3a974b3403265a",
                    "docker.io/voereir/touchstone-server-ubuntu:v3.12.0"
                ],
                "sizeBytes": 1930325107
            },
            {
                "names": [
                    "docker.io/openebs/tests-custom-client@sha256:96c262b5f3465015a11d0ac8db4a336762fe1785c81d3821584dcb3c2b083054",
                    "docker.io/openebs/tests-custom-client:latest"
                ],
                "sizeBytes": 349791077
            },
            {
                "names": [
                    "projects.registry.vmware.com/tkg/antrea-advanced-debian@sha256:c4ad5f9e8d846daf6fa80f79ed61c88aa60bc03a49e8a6b4b1fad21841ec5275"
                ],
                "sizeBytes": 271957682
            },
            {
                "names": [
                    "docker.io/litmuschaos/go-runner@sha256:b4aaa2ee36bf687dd0f147ced7dce708398fae6d8410067c9ad9a90f162d55e5",
                    "docker.io/litmuschaos/go-runner:2.14.0"
                ],
                "sizeBytes": 170207512
            },
            {
                "names": [
                    "projects.registry.vmware.com/tkg/etcd:v3.5.6_vmware.20"
                ],
                "sizeBytes": 142673295
            },
            {
                "names": [
                    "docker.io/litmuschaos/go-runner@sha256:120c92c843098f4d05f8fd5dbd6f0728ae149db851becef42383c4ca64bf847e",
                    "docker.io/litmuschaos/go-runner:2.0.0"
                ],
                "sizeBytes": 139676407
            },
            {
                "names": [
                    "docker.io/litmuschaos/go-runner@sha256:1d96f8933358c42cc1c2542869f39ce63307e6093329dbcf9dad782d3fad72a3",
                    "docker.io/litmuschaos/go-runner:1.13.8"
                ],
                "sizeBytes": 137502418
            },
            {
                "names": [
                    "projects.registry.vmware.com/tkg/kube-apiserver:v1.26.8_vmware.1"
                ],
                "sizeBytes": 137331248
            },
            {
                "names": [
                    "projects.registry.vmware.com/tkg/kube-controller-manager:v1.26.8_vmware.1"
                ],
                "sizeBytes": 126394534
            },
            {
                "names": [
                    "projects.registry.vmware.com/tkg/csi/vsphere-block-csi-driver@sha256:c3dfbbd85dd5cac17bf694c1acdbde135c5c9aa4433e57cfb6c2137e494305bb"
                ],
                "sizeBytes": 107865128
            },
            {
                "names": [
                    "docker.io/dougbtv/centos-network@sha256:74cb74f6fe64f49037d3460f60003ea6e7455ce0c7646b2badcf5a8f0811f397",
                    "docker.io/dougbtv/centos-network:latest"
                ],
                "sizeBytes": 103741563
            },
            {
                "names": [
                    "docker.io/nginxinc/nginx-unprivileged@sha256:9af8bb104ae7ded69ce009adcf76b246c6041be56bd6d09c6677f5267223bd38"
                ],
                "sizeBytes": 70523647
            },
            {
                "names": [
                    "docker.io/nginxinc/nginx-unprivileged@sha256:0c0ebe80bcaa383913d02fdc909373f89321977dd269472895c187afcd0777eb",
                    "docker.io/nginxinc/nginx-unprivileged:latest"
                ],
                "sizeBytes": 70523561
            },
            {
                "names": [
                    "docker.io/library/nginx@sha256:4c0fdaa8b6341bfdeca5f18f7837462c80cff90527ee35ef185571e1c327beac",
                    "docker.io/library/nginx:latest"
                ],
                "sizeBytes": 70520324
            },
            {
                "names": [
                    "projects.registry.vmware.com/tkg/kube-proxy:v1.26.8_vmware.1"
                ],
                "sizeBytes": 65403925
            },
            {
                "names": [
                    "projects.registry.vmware.com/tkg/kube-scheduler:v1.26.8_vmware.1"
                ],
                "sizeBytes": 58929829
            },
            {
                "names": [
                    "docker.io/litmuschaos/chaos-operator@sha256:36fcafe81d07c174aa596f80c53ad7513dc21687868060a414d004f19bcf010b",
                    "docker.io/litmuschaos/chaos-operator:1.13.8"
                ],
                "sizeBytes": 58244634
            },
            {
                "names": [
                    "docker.io/litmuschaos/chaos-runner@sha256:b437af87d294f97dde7e1db1cd3c495ce7257c9039b698736956f71a703a5c57",
                    "docker.io/litmuschaos/chaos-runner:1.13.8"
                ],
                "sizeBytes": 56021673
            },
            {
                "names": [
                    "vmwaresaas.jfrog.io/registry/nodeconfig-daemon@sha256:a63af1da505ede9f3ff03c09e0edf36b831dfc14fcd4be49d02795ec54aefc95"
                ],
                "sizeBytes": 54877278
            },
            {
                "names": [
                    "projects.registry.vmware.com/tkg/coredns:v1.9.3_vmware.16"
                ],
                "sizeBytes": 49870816
            },
            {
                "names": [
                    "projects.registry.vmware.com/tkg/whereabouts@sha256:54e87e66b501b86116ee6296bd4ba8040d922d0b3b7718192f3df393ddae1039"
                ],
                "sizeBytes": 43822425
            },
            {
                "names": [
                    "projects.registry.vmware.com/tkg/multus-cni@sha256:d378d81a80fc7910f7d452760329a2f11868876a82cc393874a85474dafa7a1d"
                ],
                "sizeBytes": 41755402
            },
            {
                "names": [
                    "projects.registry.vmware.com/tkg/metrics-server@sha256:a1ba061d6d46fa34a526690998380515583dc0f9c9dce3ea3b5aac2ac020c4c0"
                ],
                "sizeBytes": 29068608
            },
            {
                "names": [
                    "projects.registry.vmware.com/tkg/secretgen-controller@sha256:5c83a083322b2d9aae0f802923158e1aadb920c9486abee1a8c2791f3eb80bb2"
                ],
                "sizeBytes": 24083086
            },
            {
                "names": [
                    "projects.registry.vmware.com/tkg/csi/csi-node-driver-registrar@sha256:e9cd55b95d477ed887cb3266cfcd0868c8e487d4eb2f1e34a8f7183296c39776"
                ],
                "sizeBytes": 21862235
            },
            {
                "names": [
                    "docker.io/aquasec/kube-bench@sha256:959b65e754aca8f15710bff618c95c625f5d5c2d5845b04958fcf784ebfe4aea",
                    "docker.io/aquasec/kube-bench:v0.6.14"
                ],
                "sizeBytes": 21599141
            },
            {
                "names": [
                    "projects.registry.vmware.com/tkg/csi/csi-livenessprobe@sha256:b8875efc3066ec192d9e6d933b9da772fcb415e5b0d069a34e4c3d228123f9f0"
                ],
                "sizeBytes": 21364839
            },
            {
                "names": [
                    "docker.io/voereir/pod-delete-helper@sha256:7c0c5a4a92ae86796604a0b9eee99aad1059aca5ea9d964e156a547ae80f8511",
                    "docker.io/voereir/pod-delete-helper:1.13.8"
                ],
                "sizeBytes": 21192179
            },
            {
                "names": [
                    "vmwaresaas.jfrog.io/registry/nfs-subdir-external-provisioner@sha256:f741e403b3ca161e784163de3ebde9190905fdbf7dfaa463620ab8f16c0f6423"
                ],
                "sizeBytes": 17902545
            },
            {
                "names": [
                    "docker.io/library/busybox@sha256:6d9ac9237a84afe1516540f40a0fafdc86859b2141954b4d643af7066d598b74",
                    "docker.io/library/busybox:latest"
                ],
                "sizeBytes": 2231050
            },
            {
                "names": [
                    "projects.registry.vmware.com/tkg/pause:3.9"
                ],
                "sizeBytes": 739186
            },
            {
                "names": [
                    "registry.k8s.io/pause@sha256:1ff6c18fbef2045af6b9c16bf034cc421a29027b800e4f9b68ae9b1cb3e9ae07",
                    "registry.k8s.io/pause:3.5"
                ],
                "sizeBytes": 301416
            }
        ],
        "nodeInfo": {
            "architecture": "amd64",
            "bootID": "d7343011-3719-4be5-87c3-d26b89c1cb41",
            "containerRuntimeVersion": "containerd://1.6.18-1-gdbc99e5b1",
            "kernelVersion": "4.19.305-6",
            "kubeProxyVersion": "v1.26.8+vmware.1",
            "kubeletVersion": "v1.26.8+vmware.1",
            "machineID": "b62a9f7a4d0c4be19a9973122edf378d",
            "operatingSystem": "linux",
            "osImage": "VMware Photon OS/Linux",
            "systemUUID": "ced53642-e86f-5c72-2429-954c402d660c"
        }
    }
}
    """


def esxi_adapter_data():
    return """structure[0].Nic.AdminStatus.string=Up
    structure[0].Nic.DPUId.string=N/A
    structure[0].Nic.Description.string=Intel(R) Ethernet Controller X550
    structure[0].Nic.Driver.string=ixgben
    structure[0].Nic.Duplex.string=Full
    structure[0].Nic.Link.string=Up
    structure[0].Nic.LinkStatus.string=Up
    structure[0].Nic.MACAddress.string=78:ac:44:07:b2:c4
    structure[0].Nic.MTU.integer=1500
    structure[0].Nic.Name.string=vmnic0
    structure[0].Nic.PCIDevice.string=0000:18:00.0
    structure[0].Nic.Speed.integer=10000
    structure[1].Nic.AdminStatus.string=Up
    structure[1].Nic.DPUId.string=N/A
    structure[1].Nic.Description.string=Intel(R) Ethernet Controller X550
    structure[1].Nic.Driver.string=ixgben
    structure[1].Nic.Duplex.string=Full
    structure[1].Nic.Link.string=Up
    structure[1].Nic.LinkStatus.string=Up
    structure[1].Nic.MACAddress.string=78:ac:44:07:b2:c5
    structure[1].Nic.MTU.integer=1500
    structure[1].Nic.Name.string=vmnic1
    structure[1].Nic.PCIDevice.string=0000:18:00.1
    structure[1].Nic.Speed.integer=10000
    structure[2].Nic.AdminStatus.string=Up
    structure[2].Nic.DPUId.string=N/A
    structure[2].Nic.Description.string=Intel(R) I350 Gigabit Network Connection
    structure[2].Nic.Driver.string=igbn
    structure[2].Nic.Duplex.string=Half
    structure[2].Nic.Link.string=Down
    structure[2].Nic.LinkStatus.string=Down
    structure[2].Nic.MACAddress.string=78:ac:44:07:b2:c6
    structure[2].Nic.MTU.integer=1500
    structure[2].Nic.Name.string=vmnic2
    structure[2].Nic.PCIDevice.string=0000:19:00.0
    structure[2].Nic.Speed.integer=0
    structure[3].Nic.AdminStatus.string=Up
    structure[3].Nic.DPUId.string=N/A
    structure[3].Nic.Description.string=Intel(R) I350 Gigabit Network Connection
    structure[3].Nic.Driver.string=igbn
    structure[3].Nic.Duplex.string=Half
    structure[3].Nic.Link.string=Down
    structure[3].Nic.LinkStatus.string=Down
    structure[3].Nic.MACAddress.string=78:ac:44:07:b2:c7
    structure[3].Nic.MTU.integer=1500
    structure[3].Nic.Name.string=vmnic3
    structure[3].Nic.PCIDevice.string=0000:19:00.1
    structure[3].Nic.Speed.integer=0
    structure[4].Nic.AdminStatus.string=Up
    structure[4].Nic.DPUId.string=N/A
    structure[4].Nic.Description.string=Intel(R) Ethernet Controller XL710 for 40GbE QSFP+
    structure[4].Nic.Driver.string=i40en
    structure[4].Nic.Duplex.string=Full
    structure[4].Nic.Link.string=Up
    structure[4].Nic.LinkStatus.string=Up
    structure[4].Nic.MACAddress.string=f8:f2:1e:bc:f0:80
    structure[4].Nic.MTU.integer=1500
    structure[4].Nic.Name.string=vmnic4
    structure[4].Nic.PCIDevice.string=0000:3b:00.0
    structure[4].Nic.Speed.integer=40000
    structure[5].Nic.AdminStatus.string=Up
    structure[5].Nic.DPUId.string=N/A
    structure[5].Nic.Description.string=Intel(R) Ethernet Controller XL710 for 40GbE QSFP+
    structure[5].Nic.Driver.string=i40en
    structure[5].Nic.Duplex.string=Full
    structure[5].Nic.Link.string=Up
    structure[5].Nic.LinkStatus.string=Up
    structure[5].Nic.MACAddress.string=f8:f2:1e:bc:f0:81
    structure[5].Nic.MTU.integer=9000
    structure[5].Nic.Name.string=vmnic5
    structure[5].Nic.PCIDevice.string=0000:3b:00.1
    structure[5].Nic.Speed.integer=40000
    structure[6].Nic.AdminStatus.string=Up
    structure[6].Nic.DPUId.string=N/A
    structure[6].Nic.Description.string=Intel(R) Ethernet Controller XXV710 for 25GbE SFP28
    structure[6].Nic.Driver.string=i40en
    structure[6].Nic.Duplex.string=Full
    structure[6].Nic.Link.string=Up
    structure[6].Nic.LinkStatus.string=Up
    structure[6].Nic.MACAddress.string=40:a6:b7:35:6e:30
    structure[6].Nic.MTU.integer=9000
    structure[6].Nic.Name.string=vmnic6
    structure[6].Nic.PCIDevice.string=0000:88:00.0
    structure[6].Nic.Speed.integer=25000
    structure[7].Nic.AdminStatus.string=Up
    structure[7].Nic.DPUId.string=N/A
    structure[7].Nic.Description.string=Intel(R) Ethernet Controller XXV710 for 25GbE SFP28
    structure[7].Nic.Driver.string=i40en
    structure[7].Nic.Duplex.string=Full
    structure[7].Nic.Link.string=Up
    structure[7].Nic.LinkStatus.string=Up
    structure[7].Nic.MACAddress.string=40:a6:b7:35:6e:31
    structure[7].Nic.MTU.integer=1500
    structure[7].Nic.Name.string=vmnic7
    structure[7].Nic.PCIDevice.string=0000:88:00.1
    structure[7].Nic.Speed.integer=25000"""


def generate_sample_adapter_list_xml():
    return """<output xmlns="http://www.vmware.com/Products/ESX/5.0/esxcli">
<root>
   <list type="structure">
      <structure typeName="Nic">
         <field name="AdminStatus">
            <string>Up</string>
         </field>
         <field name="DPUId">
            <string>N/A</string>
         </field>
         <field name="Description">
            <string>Intel(R) Ethernet Controller X550</string>
         </field>
         <field name="Driver">
            <string>ixgben</string>
         </field>
         <field name="Duplex">
            <string>Full</string>
         </field>
         <field name="Link">
            <string>Up</string>
         </field>
         <field name="LinkStatus">
            <string>Up</string>
         </field>
         <field name="MACAddress">
            <string>78:ac:44:07:b2:c4</string>
         </field>
         <field name="MTU">
            <integer>1500</integer>
         </field>
         <field name="Name">
            <string>vmnic0</string>
         </field>
         <field name="PCIDevice">
            <string>0000:18:00.0</string>
         </field>
         <field name="Speed">
            <integer>10000</integer>
         </field>
      </structure>
      <structure typeName="Nic">
         <field name="AdminStatus">
            <string>Up</string>
         </field>
         <field name="DPUId">
            <string>N/A</string>
         </field>
         <field name="Description">
            <string>Intel(R) Ethernet Controller X550</string>
         </field>
         <field name="Driver">
            <string>ixgben</string>
         </field>
         <field name="Duplex">
            <string>Full</string>
         </field>
         <field name="Link">
            <string>Up</string>
         </field>
         <field name="LinkStatus">
            <string>Up</string>
         </field>
         <field name="MACAddress">
            <string>78:ac:44:07:b2:c5</string>
         </field>
         <field name="MTU">
            <integer>1500</integer>
         </field>
         <field name="Name">
            <string>vmnic1</string>
         </field>
         <field name="PCIDevice">
            <string>0000:18:00.1</string>
         </field>
         <field name="Speed">
            <integer>10000</integer>
         </field>
      </structure>
      <structure typeName="Nic">
         <field name="AdminStatus">
            <string>Up</string>
         </field>
         <field name="DPUId">
            <string>N/A</string>
         </field>
         <field name="Description">
            <string>Intel(R) I350 Gigabit Network Connection</string>
         </field>
         <field name="Driver">
            <string>igbn</string>
         </field>
         <field name="Duplex">
            <string>Half</string>
         </field>
         <field name="Link">
            <string>Down</string>
         </field>
         <field name="LinkStatus">
            <string>Down</string>
         </field>
         <field name="MACAddress">
            <string>78:ac:44:07:b2:c6</string>
         </field>
         <field name="MTU">
            <integer>1500</integer>
         </field>
         <field name="Name">
            <string>vmnic2</string>
         </field>
         <field name="PCIDevice">
            <string>0000:19:00.0</string>
         </field>
         <field name="Speed">
            <integer>0</integer>
         </field>
      </structure>
      <structure typeName="Nic">
         <field name="AdminStatus">
            <string>Up</string>
         </field>
         <field name="DPUId">
            <string>N/A</string>
         </field>
         <field name="Description">
            <string>Intel(R) I350 Gigabit Network Connection</string>
         </field>
         <field name="Driver">
            <string>igbn</string>
         </field>
         <field name="Duplex">
            <string>Half</string>
         </field>
         <field name="Link">
            <string>Down</string>
         </field>
         <field name="LinkStatus">
            <string>Down</string>
         </field>
         <field name="MACAddress">
            <string>78:ac:44:07:b2:c7</string>
         </field>
         <field name="MTU">
            <integer>1500</integer>
         </field>
         <field name="Name">
            <string>vmnic3</string>
         </field>
         <field name="PCIDevice">
            <string>0000:19:00.1</string>
         </field>
         <field name="Speed">
            <integer>0</integer>
         </field>
      </structure>
      <structure typeName="Nic">
         <field name="AdminStatus">
            <string>Up</string>
         </field>
         <field name="DPUId">
            <string>N/A</string>
         </field>
         <field name="Description">
            <string>Intel(R) Ethernet Controller XL710 for 40GbE QSFP+</string>
         </field>
         <field name="Driver">
            <string>i40en</string>
         </field>
         <field name="Duplex">
            <string>Full</string>
         </field>
         <field name="Link">
            <string>Up</string>
         </field>
         <field name="LinkStatus">
            <string>Up</string>
         </field>
         <field name="MACAddress">
            <string>f8:f2:1e:bc:f0:80</string>
         </field>
         <field name="MTU">
            <integer>1500</integer>
         </field>
         <field name="Name">
            <string>vmnic4</string>
         </field>
         <field name="PCIDevice">
            <string>0000:3b:00.0</string>
         </field>
         <field name="Speed">
            <integer>40000</integer>
         </field>
      </structure>
      <structure typeName="Nic">
         <field name="AdminStatus">
            <string>Up</string>
         </field>
         <field name="DPUId">
            <string>N/A</string>
         </field>
         <field name="Description">
            <string>Intel(R) Ethernet Controller XL710 for 40GbE QSFP+</string>
         </field>
         <field name="Driver">
            <string>i40en</string>
         </field>
         <field name="Duplex">
            <string>Full</string>
         </field>
         <field name="Link">
            <string>Up</string>
         </field>
         <field name="LinkStatus">
            <string>Up</string>
         </field>
         <field name="MACAddress">
            <string>f8:f2:1e:bc:f0:81</string>
         </field>
         <field name="MTU">
            <integer>9000</integer>
         </field>
         <field name="Name">
            <string>vmnic5</string>
         </field>
         <field name="PCIDevice">
            <string>0000:3b:00.1</string>
         </field>
         <field name="Speed">
            <integer>40000</integer>
         </field>
      </structure>
      <structure typeName="Nic">
         <field name="AdminStatus">
            <string>Up</string>
         </field>
         <field name="DPUId">
            <string>N/A</string>
         </field>
         <field name="Description">
            <string>Intel(R) Ethernet Controller XXV710 for 25GbE SFP28</string>
         </field>
         <field name="Driver">
            <string>i40en</string>
         </field>
         <field name="Duplex">
            <string>Full</string>
         </field>
         <field name="Link">
            <string>Up</string>
         </field>
         <field name="LinkStatus">
            <string>Up</string>
         </field>
         <field name="MACAddress">
            <string>40:a6:b7:35:6e:30</string>
         </field>
         <field name="MTU">
            <integer>9000</integer>
         </field>
         <field name="Name">
            <string>vmnic6</string>
         </field>
         <field name="PCIDevice">
            <string>0000:88:00.0</string>
         </field>
         <field name="Speed">
            <integer>25000</integer>
         </field>
      </structure>
      <structure typeName="Nic">
         <field name="AdminStatus">
            <string>Up</string>
         </field>
         <field name="DPUId">
            <string>N/A</string>
         </field>
         <field name="Description">
            <string>Intel(R) Ethernet Controller XXV710 for 25GbE SFP28</string>
         </field>
         <field name="Driver">
            <string>i40en</string>
         </field>
         <field name="Duplex">
            <string>Full</string>
         </field>
         <field name="Link">
            <string>Up</string>
         </field>
         <field name="LinkStatus">
            <string>Up</string>
         </field>
         <field name="MACAddress">
            <string>40:a6:b7:35:6e:31</string>
         </field>
         <field name="MTU">
            <integer>1500</integer>
         </field>
         <field name="Name">
            <string>vmnic7</string>
         </field>
         <field name="PCIDevice">
            <string>0000:88:00.1</string>
         </field>
         <field name="Speed">
            <integer>25000</integer>
         </field>
      </structure>
   </list>
</root>
</output>"""


def generate_sample_vm_list():
    return """<?xml version="1.0" encoding="utf-8"?>
<output xmlns="http://www.vmware.com/Products/ESX/5.0/esxcli">
<root>
   <list type="structure">
      <structure typeName="VirtualMachine">
         <field name="ConfigFile">
            <string>/vmfs/volumes/656f00b6-29f117d2-edca-78ac4407b2c6/vCLS-b4a3a15f-b274-44f1-8b47-b5de5d4093e1/vCLS-b4a3a15f-b274-44f1-8b47-b5de5d4093e1.vmx</string>
         </field>
         <field name="DisplayName">
            <string>vCLS-b4a3a15f-b274-44f1-8b47-b5de5d4093e1</string>
         </field>
         <field name="ProcessID">
            <integer>0</integer>
         </field>
         <field name="UUID">
            <string>42 36 49 50 7c 48 2a 8b-18 b5 48 e1 0d db 9a 37</string>
         </field>
         <field name="VMXCartelID">
            <integer>22541452</integer>
         </field>
         <field name="WorldID">
            <integer>22541454</integer>
         </field>
      </structure>
      <structure typeName="VirtualMachine">
         <field name="ConfigFile">
            <string>/vmfs/volumes/vsan:523d6567f1251470-01fff6533f4bec49/7c788d65-080c-0bbd-a559-78ac4407b2c6/vSAN File Service Node (2).vmx</string>
         </field>
         <field name="DisplayName">
            <string>vSAN File Service Node (2)</string>
         </field>
         <field name="ProcessID">
            <integer>0</integer>
         </field>
         <field name="UUID">
            <string>42 36 03 3c 16 95 74 01-d8 c1 cd ae 1c 2f 68 13</string>
         </field>
         <field name="VMXCartelID">
            <integer>2103347</integer>
         </field>
         <field name="WorldID">
            <integer>2103350</integer>
         </field>
      </structure>
      <structure typeName="VirtualMachine">
         <field name="ConfigFile">
            <string>/vmfs/volumes/vsan:523d6567f1251470-01fff6533f4bec49/11907165-f8d4-bc36-e1d7-78ac4407b486/vf-test-hcpdj-9x89b.vmx</string>
         </field>
         <field name="DisplayName">
            <string>vf-test-hcpdj-9x89b</string>
         </field>
         <field name="ProcessID">
            <integer>0</integer>
         </field>
         <field name="UUID">
            <string>42 36 3d 71 ec 63 af 9a-48 37 4f 25 8e 24 f2 19</string>
         </field>
         <field name="VMXCartelID">
            <integer>2105112</integer>
         </field>
         <field name="WorldID">
            <integer>2105117</integer>
         </field>
      </structure>
      <structure typeName="VirtualMachine">
         <field name="ConfigFile">
            <string>/vmfs/volumes/vsan:523d6567f1251470-01fff6533f4bec49/74738c65-740f-36b1-1cc0-e4434b62e9fe/vf-test-np1-h5mtj-9cf8fdcf6xcfln5-k9jcm.vmx</string>
         </field>
         <field name="DisplayName">
            <string>vf-test-np1-h5mtj-9cf8fdcf6xcfln5-k9jcm</string>
         </field>
         <field name="ProcessID">
            <integer>0</integer>
         </field>
         <field name="UUID">
            <string>42 36 40 fe c3 11 05 3a-47 d5 c9 7e 2c ae 7d e3</string>
         </field>
         <field name="VMXCartelID">
            <integer>2105097</integer>
         </field>
         <field name="WorldID">
            <integer>2105156</integer>
         </field>
      </structure>
      <structure typeName="VirtualMachine">
         <field name="ConfigFile">
            <string>/vmfs/volumes/vsan:523d6567f1251470-01fff6533f4bec49/0e536f65-00e0-6ba4-410f-78ac4407b2c6/TCA-M3.0.vmx</string>
         </field>
         <field name="DisplayName">
            <string>TCA-M3.0</string>
         </field>
         <field name="ProcessID">
            <integer>0</integer>
         </field>
         <field name="UUID">
            <string>42 36 3d 8b 07 77 f5 11-30 c9 4f 86 8c c4 a1 4d</string>
         </field>
         <field name="VMXCartelID">
            <integer>2292957</integer>
         </field>
         <field name="WorldID">
            <integer>2292961</integer>
         </field>
      </structure>
   </list>
</root>
</output>
    """


def generate_vf_state_data():
    return """<?xml version="1.0" encoding="utf-8"?>
<output xmlns="http://www.vmware.com/Products/ESX/5.0/esxcli">
<root>
   <list type="structure">
      <structure typeName="Nic">
         <field name="AdminStatus">
            <string>Up</string>
         </field>
         <field name="DPUId">
            <string>N/A</string>
         </field>
         <field name="Description">
            <string>Intel(R) Ethernet Controller X550</string>
         </field>
         <field name="Driver">
            <string>ixgben</string>
         </field>
         <field name="Duplex">
            <string>Full</string>
         </field>
         <field name="Link">
            <string>Up</string>
         </field>
         <field name="LinkStatus">
            <string>Up</string>
         </field>
         <field name="MACAddress">
            <string>78:ac:44:07:b2:c4</string>
         </field>
         <field name="MTU">
            <integer>1500</integer>
         </field>
         <field name="Name">
            <string>vmnic0</string>
         </field>
         <field name="PCIDevice">
            <string>0000:18:00.0</string>
         </field>
         <field name="Speed">
            <integer>10000</integer>
         </field>
      </structure>
      <structure typeName="Nic">
         <field name="AdminStatus">
            <string>Up</string>
         </field>
         <field name="DPUId">
            <string>N/A</string>
         </field>
         <field name="Description">
            <string>Intel(R) Ethernet Controller X550</string>
         </field>
         <field name="Driver">
            <string>ixgben</string>
         </field>
         <field name="Duplex">
            <string>Full</string>
         </field>
         <field name="Link">
            <string>Up</string>
         </field>
         <field name="LinkStatus">
            <string>Up</string>
         </field>
         <field name="MACAddress">
            <string>78:ac:44:07:b2:c5</string>
         </field>
         <field name="MTU">
            <integer>1500</integer>
         </field>
         <field name="Name">
            <string>vmnic1</string>
         </field>
         <field name="PCIDevice">
            <string>0000:18:00.1</string>
         </field>
         <field name="Speed">
            <integer>10000</integer>
         </field>
      </structure>
      <structure typeName="Nic">
         <field name="AdminStatus">
            <string>Up</string>
         </field>
         <field name="DPUId">
            <string>N/A</string>
         </field>
         <field name="Description">
            <string>Intel(R) I350 Gigabit Network Connection</string>
         </field>
         <field name="Driver">
            <string>igbn</string>
         </field>
         <field name="Duplex">
            <string>Half</string>
         </field>
         <field name="Link">
            <string>Down</string>
         </field>
         <field name="LinkStatus">
            <string>Down</string>
         </field>
         <field name="MACAddress">
            <string>78:ac:44:07:b2:c6</string>
         </field>
         <field name="MTU">
            <integer>1500</integer>
         </field>
         <field name="Name">
            <string>vmnic2</string>
         </field>
         <field name="PCIDevice">
            <string>0000:19:00.0</string>
         </field>
         <field name="Speed">
            <integer>0</integer>
         </field>
      </structure>
      <structure typeName="Nic">
         <field name="AdminStatus">
            <string>Up</string>
         </field>
         <field name="DPUId">
            <string>N/A</string>
         </field>
         <field name="Description">
            <string>Intel(R) I350 Gigabit Network Connection</string>
         </field>
         <field name="Driver">
            <string>igbn</string>
         </field>
         <field name="Duplex">
            <string>Half</string>
         </field>
         <field name="Link">
            <string>Down</string>
         </field>
         <field name="LinkStatus">
            <string>Down</string>
         </field>
         <field name="MACAddress">
            <string>78:ac:44:07:b2:c7</string>
         </field>
         <field name="MTU">
            <integer>1500</integer>
         </field>
         <field name="Name">
            <string>vmnic3</string>
         </field>
         <field name="PCIDevice">
            <string>0000:19:00.1</string>
         </field>
         <field name="Speed">
            <integer>0</integer>
         </field>
      </structure>
      <structure typeName="Nic">
         <field name="AdminStatus">
            <string>Up</string>
         </field>
         <field name="DPUId">
            <string>N/A</string>
         </field>
         <field name="Description">
            <string>Intel(R) Ethernet Controller XL710 for 40GbE QSFP+</string>
         </field>
         <field name="Driver">
            <string>i40en</string>
         </field>
         <field name="Duplex">
            <string>Full</string>
         </field>
         <field name="Link">
            <string>Up</string>
         </field>
         <field name="LinkStatus">
            <string>Up</string>
         </field>
         <field name="MACAddress">
            <string>f8:f2:1e:bc:f0:80</string>
         </field>
         <field name="MTU">
            <integer>1500</integer>
         </field>
         <field name="Name">
            <string>vmnic4</string>
         </field>
         <field name="PCIDevice">
            <string>0000:3b:00.0</string>
         </field>
         <field name="Speed">
            <integer>40000</integer>
         </field>
      </structure>
      <structure typeName="Nic">
         <field name="AdminStatus">
            <string>Up</string>
         </field>
         <field name="DPUId">
            <string>N/A</string>
         </field>
         <field name="Description">
            <string>Intel(R) Ethernet Controller XL710 for 40GbE QSFP+</string>
         </field>
         <field name="Driver">
            <string>i40en</string>
         </field>
         <field name="Duplex">
            <string>Full</string>
         </field>
         <field name="Link">
            <string>Up</string>
         </field>
         <field name="LinkStatus">
            <string>Up</string>
         </field>
         <field name="MACAddress">
            <string>f8:f2:1e:bc:f0:81</string>
         </field>
         <field name="MTU">
            <integer>9000</integer>
         </field>
         <field name="Name">
            <string>vmnic5</string>
         </field>
         <field name="PCIDevice">
            <string>0000:3b:00.1</string>
         </field>
         <field name="Speed">
            <integer>40000</integer>
         </field>
      </structure>
      <structure typeName="Nic">
         <field name="AdminStatus">
            <string>Up</string>
         </field>
         <field name="DPUId">
            <string>N/A</string>
         </field>
         <field name="Description">
            <string>Intel(R) Ethernet Controller XXV710 for 25GbE SFP28</string>
         </field>
         <field name="Driver">
            <string>i40en</string>
         </field>
         <field name="Duplex">
            <string>Full</string>
         </field>
         <field name="Link">
            <string>Up</string>
         </field>
         <field name="LinkStatus">
            <string>Up</string>
         </field>
         <field name="MACAddress">
            <string>40:a6:b7:35:6e:30</string>
         </field>
         <field name="MTU">
            <integer>9000</integer>
         </field>
         <field name="Name">
            <string>vmnic6</string>
         </field>
         <field name="PCIDevice">
            <string>0000:88:00.0</string>
         </field>
         <field name="Speed">
            <integer>25000</integer>
         </field>
      </structure>
      <structure typeName="Nic">
         <field name="AdminStatus">
            <string>Up</string>
         </field>
         <field name="DPUId">
            <string>N/A</string>
         </field>
         <field name="Description">
            <string>Intel(R) Ethernet Controller XXV710 for 25GbE SFP28</string>
         </field>
         <field name="Driver">
            <string>i40en</string>
         </field>
         <field name="Duplex">
            <string>Full</string>
         </field>
         <field name="Link">
            <string>Up</string>
         </field>
         <field name="LinkStatus">
            <string>Up</string>
         </field>
         <field name="MACAddress">
            <string>40:a6:b7:35:6e:31</string>
         </field>
         <field name="MTU">
            <integer>1500</integer>
         </field>
         <field name="Name">
            <string>vmnic7</string>
         </field>
         <field name="PCIDevice">
            <string>0000:88:00.1</string>
         </field>
         <field name="Speed">
            <integer>25000</integer>
         </field>
      </structure>
   </list>
</root>
</output>
"""


def generate_nic_data():
    return """<?xml version="1.0" encoding="utf-8"?>
    <output xmlns="http://www.vmware.com/Products/ESX/5.0/esxcli">
    <root>
       <structure typeName="NICInfo">
          <field name="AdvertisedAutoNegotiation">
             <boolean>true</boolean>
          </field>
          <field name="AdvertisedLinkModes">
             <list type="string">
                <string>Auto</string>
                <string>100BaseT/Full</string>
                <string>1000BaseT/Full</string>
                <string>2500BaseT/Full</string>
                <string>5000BaseT/Full</string>
                <string>10000BaseT/Full</string>
             </list>
          </field>
          <field name="AutoNegotiation">
             <boolean>true</boolean>
          </field>
          <field name="BackingDPUId">
             <string>N/A</string>
          </field>
          <field name="CableType">
             <string>Twisted Pair</string>
          </field>
          <field name="CurrentMessageLevel">
             <integer>0</integer>
          </field>
          <field name="DriverInfo">
             <structure typeName="NICDriverInfo">
                <field name="BusInfo">
                   <string>0000:18:00:0</string>
                </field>
                <field name="Driver">
                   <string>ixgben</string>
                </field>
                <field name="FirmwareVersion">
                   <string>3.30 0x800014a5, 20.5.15</string>
                </field>
                <field name="Version">
                   <string>1.15.1.0</string>
                </field>
             </structure>
          </field>
          <field name="LinkDetected">
             <boolean>true</boolean>
          </field>
          <field name="LinkStatus">
             <string>Up </string>
          </field>
          <field name="Name">
             <string>vmnic0</string>
          </field>
          <field name="PHYAddress">
             <integer>0</integer>
          </field>
          <field name="PauseAutonegotiate">
             <boolean>false</boolean>
          </field>
          <field name="PauseRX">
             <boolean>true</boolean>
          </field>
          <field name="PauseTX">
             <boolean>true</boolean>
          </field>
          <field name="SupportedPorts">
             <list type="string">
                <string>TP</string>
             </list>
          </field>
          <field name="SupportsAutoNegotiation">
             <boolean>true</boolean>
          </field>
          <field name="SupportsPause">
             <boolean>true</boolean>
          </field>
          <field name="SupportsWakeon">
             <boolean>true</boolean>
          </field>
          <field name="Transceiver">
             <string></string>
          </field>
          <field name="VirtualAddress">
             <string>00:50:56:58:e5:65</string>
          </field>
          <field name="Wakeon">
             <list type="string">
                <string>MagicPacket(tm)</string>
             </list>
          </field>
       </structure>
    </root>
    </output>"""
