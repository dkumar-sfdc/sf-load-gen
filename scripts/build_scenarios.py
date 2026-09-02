#!/usr/bin/env python3
"""Generate scenario JMeter test plans (sales/service/agent) from a shared
login base. Keeps all scenarios structurally identical for a common repo:
  Managers -> Users CSV -> Scenario data CSV -> ThreadGroup
    T1_Launch -> T2_Login -> T3_<Scenario> -> ThinkTimer -> T4_Logout
Run:  python3 scripts/build_scenarios.py
Writes: test-plans/jmeter/<scenario>-workload.jmx
"""
import os

OUT = os.path.join(os.path.dirname(__file__), "..", "test-plans", "jmeter")

# ---- reusable fragments -----------------------------------------------------

def user_credentials_csv():
    return """      <CSVDataSet guiclass="TestBeanGUI" testclass="CSVDataSet" testname="User Credentials CSV">
        <stringProp name="delimiter">,</stringProp>
        <stringProp name="fileEncoding">UTF-8</stringProp>
        <stringProp name="filename">${USER_FILE}</stringProp>
        <boolProp name="ignoreFirstLine">true</boolProp>
        <boolProp name="quotedData">false</boolProp>
        <boolProp name="recycle">true</boolProp>
        <stringProp name="shareMode">shareMode.thread</stringProp>
        <boolProp name="stopThread">false</boolProp>
        <stringProp name="variableNames">USERNAME,PASSWORD</stringProp>
      </CSVDataSet>
      <hashTree/>
"""


def header(title, comments, data_csv_vars, data_csv_default, users_default, include_user_csv=True):
    user_csv = user_credentials_csv() if include_user_csv else ""
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<jmeterTestPlan version="1.2" properties="5.0" jmeter="5.6.3">
  <hashTree>
    <TestPlan guiclass="TestPlanGui" testclass="TestPlan" testname="{title}">
      <stringProp name="TestPlan.comments">{comments}</stringProp>
      <elementProp name="TestPlan.user_defined_variables" elementType="Arguments" guiclass="ArgumentsPanel" testclass="Arguments" testname="User Defined Variables">
        <collectionProp name="Arguments.arguments">
          <elementProp name="MY_DOMAIN_HOST" elementType="Argument">
            <stringProp name="Argument.name">MY_DOMAIN_HOST</stringProp>
            <stringProp name="Argument.value">${{__P(my_domain_host,example--sandbox.sandbox.my.salesforce.com)}}</stringProp>
            <stringProp name="Argument.metadata">=</stringProp>
          </elementProp>
          <elementProp name="LIGHTNING_HOST" elementType="Argument">
            <stringProp name="Argument.name">LIGHTNING_HOST</stringProp>
            <stringProp name="Argument.value">${{__P(lightning_host,example--sandbox.sandbox.lightning.force.com)}}</stringProp>
            <stringProp name="Argument.metadata">=</stringProp>
          </elementProp>
          <elementProp name="API_VERSION" elementType="Argument">
            <stringProp name="Argument.name">API_VERSION</stringProp>
            <stringProp name="Argument.value">${{__P(api_version,v60.0)}}</stringProp>
            <stringProp name="Argument.metadata">=</stringProp>
          </elementProp>
          <elementProp name="USER_FILE" elementType="Argument">
            <stringProp name="Argument.name">USER_FILE</stringProp>
            <stringProp name="Argument.value">${{__P(users_file,{users_default})}}</stringProp>
            <stringProp name="Argument.metadata">=</stringProp>
          </elementProp>
          <elementProp name="DATA_FILE" elementType="Argument">
            <stringProp name="Argument.name">DATA_FILE</stringProp>
            <stringProp name="Argument.value">${{__P(data_file,{data_csv_default})}}</stringProp>
            <stringProp name="Argument.metadata">=</stringProp>
          </elementProp>
        </collectionProp>
      </elementProp>
    </TestPlan>
    <hashTree>
      <CookieManager guiclass="CookiePanel" testclass="CookieManager" testname="HTTP Cookie Manager">
        <collectionProp name="CookieManager.cookies"/>
        <boolProp name="CookieManager.clearEachIteration">true</boolProp>
        <boolProp name="CookieManager.controlledByThreadGroup">false</boolProp>
      </CookieManager>
      <hashTree/>
      <CacheManager guiclass="CacheManagerGui" testclass="CacheManager" testname="HTTP Cache Manager">
        <boolProp name="clearEachIteration">true</boolProp>
        <boolProp name="useExpires">true</boolProp>
        <boolProp name="CacheManager.controlledByThread">false</boolProp>
      </CacheManager>
      <hashTree/>
      <HeaderManager guiclass="HeaderPanel" testclass="HeaderManager" testname="Default HTTP Header Manager" enabled="true">
        <collectionProp name="HeaderManager.headers">
          <elementProp name="User-Agent" elementType="Header">
            <stringProp name="Header.name">User-Agent</stringProp>
            <stringProp name="Header.value">Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/146.0.0.0 Safari/537.36</stringProp>
          </elementProp>
          <elementProp name="Accept-Language" elementType="Header">
            <stringProp name="Header.name">Accept-Language</stringProp>
            <stringProp name="Header.value">en-US,en;q=0.9</stringProp>
          </elementProp>
          <elementProp name="Accept-Encoding" elementType="Header">
            <stringProp name="Header.name">Accept-Encoding</stringProp>
            <stringProp name="Header.value">gzip, deflate, br</stringProp>
          </elementProp>
        </collectionProp>
      </HeaderManager>
      <hashTree/>
{user_csv}      <CSVDataSet guiclass="TestBeanGUI" testclass="CSVDataSet" testname="Scenario Data CSV">
        <stringProp name="delimiter">,</stringProp>
        <stringProp name="fileEncoding">UTF-8</stringProp>
        <stringProp name="filename">${{DATA_FILE}}</stringProp>
        <boolProp name="ignoreFirstLine">true</boolProp>
        <boolProp name="quotedData">true</boolProp>
        <boolProp name="recycle">true</boolProp>
        <stringProp name="shareMode">shareMode.all</stringProp>
        <boolProp name="stopThread">false</boolProp>
        <stringProp name="variableNames">{data_csv_vars}</stringProp>
      </CSVDataSet>
      <hashTree/>
      <Arguments guiclass="ArgumentsPanel" testclass="Arguments" testname="Tuning Variables">
        <collectionProp name="Arguments.arguments">
          <elementProp name="THINK_TIME" elementType="Argument">
            <stringProp name="Argument.name">THINK_TIME</stringProp>
            <stringProp name="Argument.value">${{__P(think_time,2000)}}</stringProp>
            <stringProp name="Argument.metadata">=</stringProp>
          </elementProp>
        </collectionProp>
      </Arguments>
      <hashTree/>
"""


def setup_thread_group():
    # setUp Thread Group: run once before the main group. Loads each Username -> Password
    # from the user-file into JMeter properties so the task can resolve the password for
    # the login username carried on each business-data row. (pattern ref: GRAB-TASK1)
    return """      <SetupThreadGroup guiclass="SetupThreadGroupGui" testclass="SetupThreadGroup" testname="setUp - Load Credentials" enabled="true">
        <intProp name="ThreadGroup.num_threads">1</intProp>
        <intProp name="ThreadGroup.ramp_time">1</intProp>
        <boolProp name="ThreadGroup.same_user_on_next_iteration">true</boolProp>
        <stringProp name="ThreadGroup.on_sample_error">stopthread</stringProp>
        <elementProp name="ThreadGroup.main_controller" elementType="LoopController" guiclass="LoopControlPanel" testclass="LoopController" testname="Loop Controller">
          <stringProp name="LoopController.loops">1</stringProp>
          <boolProp name="LoopController.continue_forever">false</boolProp>
        </elementProp>
      </SetupThreadGroup>
      <hashTree>
        <JSR223Sampler guiclass="TestBeanGUI" testclass="JSR223Sampler" testname="Load user-file into properties" enabled="true">
          <stringProp name="cacheKey">true</stringProp>
          <stringProp name="filename"></stringProp>
          <stringProp name="parameters"></stringProp>
          <stringProp name="script">import org.apache.jmeter.services.FileServer

// The plan has to run wherever it is dropped on the VM, so try the path as given
// (absolute, or relative to the working directory) and then relative to this .jmx.
def path = vars.get(&quot;USER_FILE&quot;)
def candidates = [new File(path), new File(FileServer.getFileServer().getBaseDir(), path)]
def file = candidates.find { it.isFile() }
if (file == null) {
  SampleResult.setSuccessful(false)
  SampleResult.setResponseData(&quot;credentials loaded: 0&quot;, &quot;UTF-8&quot;)
  SampleResult.setResponseMessage(&quot;No user file at &quot; + candidates.collect { it.getAbsolutePath() }.join(&quot; or &quot;))
  return
}

int loaded = 0
file.readLines().drop(1).each { line -&gt;
  def row = line.trim()
  if (row.length() != 0) {
    def cols = row.split(&quot;,&quot;, -1)
    if (cols.length &gt;= 2) {
      props.put(&quot;password.&quot; + cols[0].trim(), cols[1].trim())
      loaded++
    }
  }
}

SampleResult.setResponseData(&quot;credentials loaded: &quot; + loaded, &quot;UTF-8&quot;)
SampleResult.setDataType(&quot;text&quot;)
SampleResult.setSuccessful(loaded != 0)
if (loaded == 0) {
  SampleResult.setResponseMessage(&quot;No credentials found in &quot; + file.getAbsolutePath())
}</stringProp>
          <stringProp name="scriptLanguage">groovy</stringProp>
        </JSR223Sampler>
        <hashTree/>
      </hashTree>
"""


def thread_group_open(title):
    return f"""      <ThreadGroup guiclass="ThreadGroupGui" testclass="ThreadGroup" testname="{title} Thread Group" enabled="true">
        <stringProp name="ThreadGroup.num_threads">${{__P(threads,10)}}</stringProp>
        <stringProp name="ThreadGroup.ramp_time">${{__P(ramp,30)}}</stringProp>
        <boolProp name="ThreadGroup.same_user_on_next_iteration">true</boolProp>
        <stringProp name="ThreadGroup.on_sample_error">continue</stringProp>
        <elementProp name="ThreadGroup.main_controller" elementType="LoopController" guiclass="LoopControlPanel" testclass="LoopController" testname="Loop Controller">
          <stringProp name="LoopController.loops">${{__P(loops,1)}}</stringProp>
          <boolProp name="LoopController.continue_forever">false</boolProp>
        </elementProp>
      </ThreadGroup>
      <hashTree>
"""


def resolve_password_preproc():
    # Per-iteration: map the business-row login Username -> USERNAME/PASSWORD used by T2_Login.
    # Password looked up from properties loaded by the setUp Thread Group (key: password.<username>).
    return """        <JSR223PreProcessor guiclass="TestBeanGUI" testclass="JSR223PreProcessor" testname="Resolve Password for row Username" enabled="true">
          <stringProp name="cacheKey">true</stringProp>
          <stringProp name="filename"></stringProp>
          <stringProp name="parameters"></stringProp>
          <stringProp name="script">// Scenario Data CSV supplies 'Username' as its first column. Resolve the matching
// password loaded by the setUp Thread Group and expose USERNAME/PASSWORD for login.
def user = vars.get(&quot;Username&quot;)
def password = props.get(&quot;password.&quot; + user)
if (password == null) {
  log.error(&quot;No password in user-file for username: &quot; + user)
  password = &quot;&quot;
}
vars.put(&quot;USERNAME&quot;, user)
vars.put(&quot;PASSWORD&quot;, password)</stringProp>
          <stringProp name="scriptLanguage">groovy</stringProp>
        </JSR223PreProcessor>
        <hashTree/>
"""


LOGIN = """        <TransactionController guiclass="TransactionControllerGui" testclass="TransactionController" testname="T1_Launch" enabled="true">
          <boolProp name="TransactionController.parent">true</boolProp>
          <boolProp name="TransactionController.includeTimers">false</boolProp>
        </TransactionController>
        <hashTree>
          <HTTPSamplerProxy guiclass="HttpTestSampleGui" testclass="HTTPSamplerProxy" testname="GET Lightning landing">
            <stringProp name="HTTPSampler.domain">${LIGHTNING_HOST}</stringProp>
            <stringProp name="HTTPSampler.port">443</stringProp>
            <stringProp name="HTTPSampler.protocol">https</stringProp>
            <stringProp name="HTTPSampler.path">/</stringProp>
            <boolProp name="HTTPSampler.follow_redirects">true</boolProp>
            <stringProp name="HTTPSampler.method">GET</stringProp>
            <boolProp name="HTTPSampler.use_keepalive">true</boolProp>
            <boolProp name="HTTPSampler.postBodyRaw">false</boolProp>
            <elementProp name="HTTPsampler.Arguments" elementType="Arguments" guiclass="HTTPArgumentsPanel" testclass="Arguments" testname="User Defined Variables">
              <collectionProp name="Arguments.arguments"/>
            </elementProp>
          </HTTPSamplerProxy>
          <hashTree/>
          <HTTPSamplerProxy guiclass="HttpTestSampleGui" testclass="HTTPSamplerProxy" testname="GET My Domain login page">
            <stringProp name="HTTPSampler.domain">${MY_DOMAIN_HOST}</stringProp>
            <stringProp name="HTTPSampler.port">443</stringProp>
            <stringProp name="HTTPSampler.protocol">https</stringProp>
            <stringProp name="HTTPSampler.path">/</stringProp>
            <boolProp name="HTTPSampler.follow_redirects">true</boolProp>
            <stringProp name="HTTPSampler.method">GET</stringProp>
            <boolProp name="HTTPSampler.use_keepalive">true</boolProp>
            <boolProp name="HTTPSampler.postBodyRaw">false</boolProp>
            <elementProp name="HTTPsampler.Arguments" elementType="Arguments" guiclass="HTTPArgumentsPanel" testclass="Arguments" testname="User Defined Variables">
              <collectionProp name="Arguments.arguments"/>
            </elementProp>
          </HTTPSamplerProxy>
          <hashTree/>
        </hashTree>
        <TransactionController guiclass="TransactionControllerGui" testclass="TransactionController" testname="T2_Login" enabled="true">
          <boolProp name="TransactionController.parent">true</boolProp>
          <boolProp name="TransactionController.includeTimers">false</boolProp>
        </TransactionController>
        <hashTree>
          <HTTPSamplerProxy guiclass="HttpTestSampleGui" testclass="HTTPSamplerProxy" testname="POST username and password">
            <stringProp name="HTTPSampler.domain">${MY_DOMAIN_HOST}</stringProp>
            <stringProp name="HTTPSampler.port">443</stringProp>
            <stringProp name="HTTPSampler.protocol">https</stringProp>
            <stringProp name="HTTPSampler.contentEncoding">UTF-8</stringProp>
            <stringProp name="HTTPSampler.path">/</stringProp>
            <boolProp name="HTTPSampler.follow_redirects">false</boolProp>
            <boolProp name="HTTPSampler.auto_redirects">false</boolProp>
            <stringProp name="HTTPSampler.method">POST</stringProp>
            <boolProp name="HTTPSampler.use_keepalive">true</boolProp>
            <boolProp name="HTTPSampler.postBodyRaw">false</boolProp>
            <elementProp name="HTTPsampler.Arguments" elementType="Arguments" guiclass="HTTPArgumentsPanel" testclass="Arguments" testname="User Defined Variables">
              <collectionProp name="Arguments.arguments">
                <elementProp name="un" elementType="HTTPArgument">
                  <boolProp name="HTTPArgument.always_encode">true</boolProp>
                  <stringProp name="Argument.name">un</stringProp>
                  <stringProp name="Argument.value">${USERNAME}</stringProp>
                  <stringProp name="Argument.metadata">=</stringProp>
                  <boolProp name="HTTPArgument.use_equals">true</boolProp>
                </elementProp>
                <elementProp name="pw" elementType="HTTPArgument">
                  <boolProp name="HTTPArgument.always_encode">true</boolProp>
                  <stringProp name="Argument.name">pw</stringProp>
                  <stringProp name="Argument.value">${PASSWORD}</stringProp>
                  <stringProp name="Argument.metadata">=</stringProp>
                  <boolProp name="HTTPArgument.use_equals">true</boolProp>
                </elementProp>
                <elementProp name="lt" elementType="HTTPArgument">
                  <boolProp name="HTTPArgument.always_encode">false</boolProp>
                  <stringProp name="Argument.name">lt</stringProp>
                  <stringProp name="Argument.value">standard</stringProp>
                  <stringProp name="Argument.metadata">=</stringProp>
                  <boolProp name="HTTPArgument.use_equals">true</boolProp>
                </elementProp>
                <elementProp name="useSecure" elementType="HTTPArgument">
                  <boolProp name="HTTPArgument.always_encode">false</boolProp>
                  <stringProp name="Argument.name">useSecure</stringProp>
                  <stringProp name="Argument.value">true</stringProp>
                  <stringProp name="Argument.metadata">=</stringProp>
                  <boolProp name="HTTPArgument.use_equals">true</boolProp>
                </elementProp>
                <elementProp name="display" elementType="HTTPArgument">
                  <boolProp name="HTTPArgument.always_encode">false</boolProp>
                  <stringProp name="Argument.name">display</stringProp>
                  <stringProp name="Argument.value">page</stringProp>
                  <stringProp name="Argument.metadata">=</stringProp>
                  <boolProp name="HTTPArgument.use_equals">true</boolProp>
                </elementProp>
              </collectionProp>
            </elementProp>
          </HTTPSamplerProxy>
          <hashTree>
            <HeaderManager guiclass="HeaderPanel" testclass="HeaderManager" testname="HTTP Header Manager" enabled="true">
              <collectionProp name="HeaderManager.headers">
                <elementProp name="Content-Type" elementType="Header">
                  <stringProp name="Header.name">Content-Type</stringProp>
                  <stringProp name="Header.value">application/x-www-form-urlencoded</stringProp>
                </elementProp>
                <elementProp name="Origin" elementType="Header">
                  <stringProp name="Header.name">Origin</stringProp>
                  <stringProp name="Header.value">https://${MY_DOMAIN_HOST}</stringProp>
                </elementProp>
                <elementProp name="Referer" elementType="Header">
                  <stringProp name="Header.name">Referer</stringProp>
                  <stringProp name="Header.value">https://${MY_DOMAIN_HOST}/</stringProp>
                </elementProp>
              </collectionProp>
            </HeaderManager>
            <hashTree/>
            <RegexExtractor guiclass="RegexExtractorGui" testclass="RegexExtractor" testname="Extract sid from redirect" enabled="true">
              <stringProp name="RegexExtractor.useHeaders">true</stringProp>
              <stringProp name="RegexExtractor.refname">sid</stringProp>
              <stringProp name="RegexExtractor.regex">sid=(.+?)&amp;</stringProp>
              <stringProp name="RegexExtractor.template">$1$</stringProp>
              <stringProp name="RegexExtractor.default">SID_NOT_FOUND</stringProp>
              <stringProp name="RegexExtractor.match_number">1</stringProp>
              <stringProp name="Sample.scope">all</stringProp>
              <boolProp name="RegexExtractor.default_empty_value">false</boolProp>
            </RegexExtractor>
            <hashTree/>
            <RegexExtractor guiclass="RegexExtractorGui" testclass="RegexExtractor" testname="Extract cshc from redirect" enabled="true">
              <stringProp name="RegexExtractor.useHeaders">true</stringProp>
              <stringProp name="RegexExtractor.refname">cshc</stringProp>
              <stringProp name="RegexExtractor.regex">cshc=(.+?)&amp;</stringProp>
              <stringProp name="RegexExtractor.template">$1$</stringProp>
              <stringProp name="RegexExtractor.default"></stringProp>
              <stringProp name="RegexExtractor.match_number">1</stringProp>
              <stringProp name="Sample.scope">all</stringProp>
              <boolProp name="RegexExtractor.default_empty_value">true</boolProp>
            </RegexExtractor>
            <hashTree/>
            <ResponseAssertion guiclass="AssertionGui" testclass="ResponseAssertion" testname="Assert credentials accepted" enabled="true">
              <collectionProp name="Asserion.test_strings">
                <stringProp name="sid_present">SID_NOT_FOUND</stringProp>
              </collectionProp>
              <stringProp name="Assertion.custom_message">Login POST did not return a session id (sid) - check username/password or host.</stringProp>
              <stringProp name="Assertion.test_field">Assertion.response_data</stringProp>
              <boolProp name="Assertion.assume_success">false</boolProp>
              <intProp name="Assertion.test_type">6</intProp>
              <stringProp name="Assertion.scope">variable</stringProp>
              <stringProp name="Scope.variable">sid</stringProp>
            </ResponseAssertion>
            <hashTree/>
          </hashTree>
          <HTTPSamplerProxy guiclass="HttpTestSampleGui" testclass="HTTPSamplerProxy" testname="GET frontdoor.jsp establish session">
            <stringProp name="HTTPSampler.domain">${MY_DOMAIN_HOST}</stringProp>
            <stringProp name="HTTPSampler.port">443</stringProp>
            <stringProp name="HTTPSampler.protocol">https</stringProp>
            <stringProp name="HTTPSampler.path">/secur/frontdoor.jsp</stringProp>
            <boolProp name="HTTPSampler.follow_redirects">true</boolProp>
            <stringProp name="HTTPSampler.method">GET</stringProp>
            <boolProp name="HTTPSampler.use_keepalive">true</boolProp>
            <boolProp name="HTTPSampler.postBodyRaw">false</boolProp>
            <elementProp name="HTTPsampler.Arguments" elementType="Arguments" guiclass="HTTPArgumentsPanel" testclass="Arguments" testname="User Defined Variables">
              <collectionProp name="Arguments.arguments">
                <elementProp name="sid" elementType="HTTPArgument">
                  <boolProp name="HTTPArgument.always_encode">false</boolProp>
                  <stringProp name="Argument.name">sid</stringProp>
                  <stringProp name="Argument.value">${sid}</stringProp>
                  <stringProp name="Argument.metadata">=</stringProp>
                  <boolProp name="HTTPArgument.use_equals">true</boolProp>
                </elementProp>
                <elementProp name="cshc" elementType="HTTPArgument">
                  <boolProp name="HTTPArgument.always_encode">false</boolProp>
                  <stringProp name="Argument.name">cshc</stringProp>
                  <stringProp name="Argument.value">${cshc}</stringProp>
                  <stringProp name="Argument.metadata">=</stringProp>
                  <boolProp name="HTTPArgument.use_equals">true</boolProp>
                </elementProp>
                <elementProp name="apv" elementType="HTTPArgument">
                  <boolProp name="HTTPArgument.always_encode">false</boolProp>
                  <stringProp name="Argument.name">apv</stringProp>
                  <stringProp name="Argument.value">1</stringProp>
                  <stringProp name="Argument.metadata">=</stringProp>
                  <boolProp name="HTTPArgument.use_equals">true</boolProp>
                </elementProp>
              </collectionProp>
            </elementProp>
          </HTTPSamplerProxy>
          <hashTree/>
        </hashTree>
"""

def rest_get(name, path):
    return f"""          <HTTPSamplerProxy guiclass="HttpTestSampleGui" testclass="HTTPSamplerProxy" testname="{name}">
            <stringProp name="HTTPSampler.domain">${{MY_DOMAIN_HOST}}</stringProp>
            <stringProp name="HTTPSampler.port">443</stringProp>
            <stringProp name="HTTPSampler.protocol">https</stringProp>
            <stringProp name="HTTPSampler.path">{path}</stringProp>
            <boolProp name="HTTPSampler.follow_redirects">true</boolProp>
            <stringProp name="HTTPSampler.method">GET</stringProp>
            <boolProp name="HTTPSampler.use_keepalive">true</boolProp>
            <boolProp name="HTTPSampler.postBodyRaw">false</boolProp>
            <elementProp name="HTTPsampler.Arguments" elementType="Arguments" guiclass="HTTPArgumentsPanel" testclass="Arguments" testname="User Defined Variables">
              <collectionProp name="Arguments.arguments"/>
            </elementProp>
          </HTTPSamplerProxy>
          <hashTree/>
"""

def rest_json_post(name, path, json_body, extractor=None, method="POST"):
    extra = ""
    if extractor:
        ref, regex, default = extractor
        extra = f"""            <RegexExtractor guiclass="RegexExtractorGui" testclass="RegexExtractor" testname="Extract {ref}" enabled="true">
              <stringProp name="RegexExtractor.refname">{ref}</stringProp>
              <stringProp name="RegexExtractor.regex">{regex}</stringProp>
              <stringProp name="RegexExtractor.template">$1$</stringProp>
              <stringProp name="RegexExtractor.default">{default}</stringProp>
              <stringProp name="RegexExtractor.match_number">1</stringProp>
              <boolProp name="RegexExtractor.default_empty_value">false</boolProp>
            </RegexExtractor>
            <hashTree/>
            <ResponseAssertion guiclass="AssertionGui" testclass="ResponseAssertion" testname="Assert {ref} extracted" enabled="true">
              <collectionProp name="Asserion.test_strings">
                <stringProp name="id_present">{default}</stringProp>
              </collectionProp>
              <stringProp name="Assertion.custom_message">{ref} not extracted (still {default}) - the create call failed; a downstream update/use would target a bogus id.</stringProp>
              <stringProp name="Assertion.test_field">Assertion.response_data</stringProp>
              <boolProp name="Assertion.assume_success">false</boolProp>
              <intProp name="Assertion.test_type">6</intProp>
              <stringProp name="Assertion.scope">variable</stringProp>
              <stringProp name="Scope.variable">{ref}</stringProp>
            </ResponseAssertion>
            <hashTree/>
"""
    return f"""          <HTTPSamplerProxy guiclass="HttpTestSampleGui" testclass="HTTPSamplerProxy" testname="{name}">
            <stringProp name="HTTPSampler.domain">${{MY_DOMAIN_HOST}}</stringProp>
            <stringProp name="HTTPSampler.port">443</stringProp>
            <stringProp name="HTTPSampler.protocol">https</stringProp>
            <stringProp name="HTTPSampler.contentEncoding">UTF-8</stringProp>
            <stringProp name="HTTPSampler.path">{path}</stringProp>
            <boolProp name="HTTPSampler.follow_redirects">true</boolProp>
            <stringProp name="HTTPSampler.method">{method}</stringProp>
            <boolProp name="HTTPSampler.use_keepalive">true</boolProp>
            <boolProp name="HTTPSampler.postBodyRaw">true</boolProp>
            <elementProp name="HTTPsampler.Arguments" elementType="Arguments" testclass="Arguments" testname="User Defined Variables">
              <collectionProp name="Arguments.arguments">
                <elementProp name="" elementType="HTTPArgument">
                  <boolProp name="HTTPArgument.always_encode">false</boolProp>
                  <stringProp name="Argument.value">{json_body}</stringProp>
                  <stringProp name="Argument.metadata">=</stringProp>
                </elementProp>
              </collectionProp>
            </elementProp>
          </HTTPSamplerProxy>
          <hashTree>
            <HeaderManager guiclass="HeaderPanel" testclass="HeaderManager" testname="HTTP Header Manager" enabled="true">
              <collectionProp name="HeaderManager.headers">
                <elementProp name="Content-Type" elementType="Header">
                  <stringProp name="Header.name">Content-Type</stringProp>
                  <stringProp name="Header.value">application/json</stringProp>
                </elementProp>
                <elementProp name="Authorization" elementType="Header">
                  <stringProp name="Header.name">Authorization</stringProp>
                  <stringProp name="Header.value">Bearer ${{sid}}</stringProp>
                </elementProp>
              </collectionProp>
            </HeaderManager>
            <hashTree/>
{extra}          </hashTree>
"""

def txn(name, samplers):
    return f"""        <TransactionController guiclass="TransactionControllerGui" testclass="TransactionController" testname="{name}" enabled="true">
          <boolProp name="TransactionController.parent">true</boolProp>
          <boolProp name="TransactionController.includeTimers">false</boolProp>
        </TransactionController>
        <hashTree>
{samplers}        </hashTree>
"""

THINK = """        <TestAction guiclass="TestActionGui" testclass="TestAction" testname="Think Time" enabled="true">
          <intProp name="ActionProcessor.action">1</intProp>
          <intProp name="ActionProcessor.target">0</intProp>
          <stringProp name="ActionProcessor.duration">0</stringProp>
        </TestAction>
        <hashTree>
          <UniformRandomTimer guiclass="UniformRandomTimerGui" testclass="UniformRandomTimer" testname="Think Timer" enabled="true">
            <stringProp name="ConstantTimer.delay">${THINK_TIME}</stringProp>
            <stringProp name="RandomTimer.range">1000</stringProp>
          </UniformRandomTimer>
          <hashTree/>
        </hashTree>
"""

LOGOUT_AND_FOOTER = """        <TransactionController guiclass="TransactionControllerGui" testclass="TransactionController" testname="T4_Logout" enabled="true">
          <boolProp name="TransactionController.parent">true</boolProp>
          <boolProp name="TransactionController.includeTimers">false</boolProp>
        </TransactionController>
        <hashTree>
          <HTTPSamplerProxy guiclass="HttpTestSampleGui" testclass="HTTPSamplerProxy" testname="GET logout">
            <stringProp name="HTTPSampler.domain">${MY_DOMAIN_HOST}</stringProp>
            <stringProp name="HTTPSampler.port">443</stringProp>
            <stringProp name="HTTPSampler.protocol">https</stringProp>
            <stringProp name="HTTPSampler.path">/secur/logout.jsp</stringProp>
            <boolProp name="HTTPSampler.follow_redirects">true</boolProp>
            <stringProp name="HTTPSampler.method">GET</stringProp>
            <boolProp name="HTTPSampler.use_keepalive">true</boolProp>
            <boolProp name="HTTPSampler.postBodyRaw">false</boolProp>
            <elementProp name="HTTPsampler.Arguments" elementType="Arguments" guiclass="HTTPArgumentsPanel" testclass="Arguments" testname="User Defined Variables">
              <collectionProp name="Arguments.arguments"/>
            </elementProp>
          </HTTPSamplerProxy>
          <hashTree/>
        </hashTree>
        <ResultCollector guiclass="ViewResultsFullVisualizer" testclass="ResultCollector" testname="View Results Tree" enabled="true">
          <boolProp name="ResultCollector.error_logging">false</boolProp>
          <objProp>
            <name>saveConfig</name>
            <value class="SampleSaveConfiguration">
              <time>true</time><latency>true</latency><timestamp>true</timestamp>
              <success>true</success><label>true</label><code>true</code>
              <message>true</message><threadName>true</threadName><dataType>true</dataType>
              <assertions>true</assertions><subresults>true</subresults><responseData>false</responseData>
              <samplerData>false</samplerData><xml>false</xml><fieldNames>true</fieldNames>
              <responseHeaders>false</responseHeaders><requestHeaders>false</requestHeaders>
              <responseDataOnError>false</responseDataOnError>
              <saveAssertionResultsFailureMessage>true</saveAssertionResultsFailureMessage>
              <assertionsResultsToSave>0</assertionsResultsToSave><bytes>true</bytes>
              <sentBytes>true</sentBytes><url>true</url><threadCounts>true</threadCounts>
              <idleTime>true</idleTime><connectTime>true</connectTime>
            </value>
          </objProp>
          <stringProp name="filename"></stringProp>
        </ResultCollector>
        <hashTree/>
      </hashTree>
    </hashTree>
  </hashTree>
</jmeterTestPlan>
"""

# ---- scenarios --------------------------------------------------------------

SCENARIOS = {
    "sales": {
        "title": "Sales Workload Load Test",
        "comments": "Login + Sales Cloud journey: create a Lead then update it via REST. Tasks: launch, login, create lead, update lead, logout.",
        "users_default": "../../user-files/sales_users.csv",
        "data_default": "../../data-files/sales_leads.csv",
        # First column 'Username' is the login user; the setUp group + resolve PreProcessor
        # map it to a password from sales_users.csv.
        "data_vars": "Username,Company,LastName,FirstName,Email,Phone,LeadStatus,UpdatedStatus",
        "resolve_password": True,
        "txn_name": "T3_Create_Lead",
        "samplers": rest_json_post(
            "POST create Lead",
            "/services/data/${API_VERSION}/sobjects/Lead",
            '{"Company":"${Company}","LastName":"${LastName}","FirstName":"${FirstName}","Email":"${Email}","Phone":"${Phone}","Status":"${LeadStatus}"}',
            extractor=("leadId", '"id"\\s*:\\s*"(.+?)"', "LEAD_ID_NOT_FOUND"),
        ),
        # Second business txn: update the Lead just created (PATCH -> 204 No Content).
        "extra_txns": txn(
            "T3_Update_Lead",
            rest_json_post(
                "PATCH update Lead",
                "/services/data/${API_VERSION}/sobjects/Lead/${leadId}",
                '{"Status":"${UpdatedStatus}","Phone":"${Phone}"}',
                method="PATCH",
            ),
        ),
    },
    "service": {
        "title": "Service Workload Load Test",
        "comments": "Login + Service Cloud journey: create a Case then update it via REST. Tasks: launch, login, create case, update case, logout.",
        "users_default": "../../user-files/service_users.csv",
        "data_default": "../../data-files/service_cases.csv",
        "data_vars": "Subject,Description,Priority,Origin,Status,UpdatedStatus,ContactEmail",
        "txn_name": "T3_Create_Case",
        "samplers": rest_json_post(
            "POST create Case",
            "/services/data/${API_VERSION}/sobjects/Case",
            '{"Subject":"${Subject}","Description":"${Description}","Priority":"${Priority}","Origin":"${Origin}","Status":"${Status}"}',
            extractor=("caseId", '"id"\\s*:\\s*"(.+?)"', "CASE_ID_NOT_FOUND"),
        ),
        # Second business txn: update the Case just created (PATCH -> 204 No Content).
        "extra_txns": txn(
            "T3_Update_Case",
            rest_json_post(
                "PATCH update Case",
                "/services/data/${API_VERSION}/sobjects/Case/${caseId}",
                '{"Status":"${UpdatedStatus}","Priority":"${Priority}"}',
                method="PATCH",
            ),
        ),
    },
    "agent": {
        "title": "Agent Workload Load Test",
        "comments": "Login + Agentforce journey: start an agent session, send an utterance, end session.",
        "users_default": "../../user-files/agent_users.csv",
        "data_default": "../../data-files/agent_prompts.csv",
        "data_vars": "SessionLabel,UtteranceText,ExpectedTopic",
        "txn_name": "T3_Agent",
        "samplers": (
            rest_json_post(
                "POST start agent session",
                "/einstein/ai-agent/v1/agents/${__P(agent_id,0XxSB000000mockAgentId)}/sessions",
                '{"externalSessionKey":"${SessionLabel}-${__threadNum}","instanceConfig":{"endpoint":"https://${MY_DOMAIN_HOST}"},"streamingCapabilities":{"chunkTypes":["Text"]}}',
                extractor=("agentSessionId", '"sessionId"\\s*:\\s*"(.+?)"', "SESSION_ID_NOT_FOUND"),
            )
            + rest_json_post(
                "POST send utterance",
                "/einstein/ai-agent/v1/sessions/${agentSessionId}/messages",
                '{"message":{"sequenceId":1,"type":"Text","text":"${UtteranceText}"}}',
            )
            + rest_json_post(
                "POST end agent session",
                "/einstein/ai-agent/v1/sessions/${agentSessionId}/end",
                '{"reason":"UserRequest"}',
            )
        ),
    },
}

def build():
    os.makedirs(OUT, exist_ok=True)
    for key, s in SCENARIOS.items():
        resolve = s.get("resolve_password", False)
        doc = (
            header(s["title"], s["comments"], s["data_vars"], s["data_default"],
                   s["users_default"], include_user_csv=not resolve)
            + (setup_thread_group() if resolve else "")
            + thread_group_open(s["title"])
            + (resolve_password_preproc() if resolve else "")
            + LOGIN
            + txn(s["txn_name"], s["samplers"])
            + s.get("extra_txns", "")
            + THINK
            + LOGOUT_AND_FOOTER
        )
        path = os.path.join(OUT, f"{key}-workload.jmx")
        with open(path, "w") as f:
            f.write(doc)
        print("wrote", os.path.relpath(path))

if __name__ == "__main__":
    build()
