<?xml version="1.0"?>
<xsl:stylesheet version="1.0"
  xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
  xmlns:odm="http://www.cdisc.org/ns/odm/v1.3"
  xmlns:osb="http://www.openstudybuilder.org">

  <xsl:output method="html"/>
  <xsl:template match="/">
    <html>
      <head>
        <title><xsl:value-of select="/ODM/Study/@OID"/></title>
        <link rel="stylesheet" href="https://stackpath.bootstrapcdn.com/bootstrap/4.3.1/css/bootstrap.min.css" />
        <link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:opsz,wght,FILL,GRAD@48,700,1,200" />
        <style>
          em {
          font-weight: bold;
          font-style: normal;
          color: #f00;
          }
          .online-help {
          color: grey;
          font-style: italic;
          padding-left: 30px;
          }
          .container {
          max-width: 100%;
          }
          .v-application ul {
          padding-left: 0px;
          display: flex;
          align-items: center;
          }
          .material-symbols-outlined {
          vertical-align: text-bottom;
          }
          .form-group {
          margin-bottom: -1rem;
          }
          .col-form-label {
          text-align: end;
          }
          .item-title {
          font-weight: 500;
          color: black;
          }
          .notLockItem {
          color: green;
          }
          .alert-green {
          color: green;
          }
        </style>
      </head>
      <body>
        <div class="container">
          <div class="row">
            <div class="col-10">
              <h2><xsl:value-of select="/ODM/Study/GlobalVariables/StudyName"/></h2>
            </div>
            <div class="col-2">
              <h2>Blank CRF</h2>
            </div>
          </div>
          <xsl:apply-templates select="/ODM/Study/MetaDataVersion/FormDef"/>
        </div>
        <script src="https://code.jquery.com/jquery-3.3.1.slim.min.js" integrity="sha384-q8i/X+965DzO0rT7abK41JStQIAqVgRVzpbzo5smXKp4YfRvH+8abtTE1Pi6jizo" crossorigin="anonymous"></script>
        <script src="https://cdn.jsdelivr.net/npm/@popperjs/core@2.11.6/dist/umd/popper.min.js" integrity="sha384-oBqDVmMz9ATKxIep9tiCxS/Z9fNfEXiDAYTujMAeBAsjFuCZSmKbSSUnQlmh/jp3" crossorigin="anonymous"></script>
        <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.2.2/dist/js/bootstrap.min.js" integrity="sha384-IDwe1+LCz02ROU9k972gdyvl+AESN10+x7tBKgc9I5HFtuNz0wWnPclzo6p9vxnk" crossorigin="anonymous"></script>
      </body>
    </html>
  </xsl:template>

  <xsl:template match="ItemDef">
    <xsl:param name="domainNiv" />
    <xsl:param name="itemCondition" />
    <xsl:variable name="displayType">
      <xsl:choose>
        <xsl:when test="./Alias/@Context = 'CTDisplay'">Checkbox</xsl:when>
        <xsl:when test="./@osb:allowsMultiChoice = 'True'">Checkbox</xsl:when>
        <xsl:otherwise>Radio</xsl:otherwise> <!-- default value -->
      </xsl:choose>
    </xsl:variable>

    <div class="container">
      <xsl:choose>
        <xsl:when test="./@DataType = 'comment'"> <!-- Title -->
          <div class="row">
            <div class="col-3 border text-right" /> <!-- Item lable column -->
            <div class="col-9 border text-left">
              <xsl:choose>
                <xsl:when test="./Question">
                  <xsl:choose>
                    <xsl:when test="$itemCondition != 'null'">
                      <span class="material-symbols-outlined alert-green">subdirectory_arrow_right</span>&#160;
                      <xsl:apply-templates select="Question">
                        <xsl:with-param name="lockItem" select="'No'" />
                      </xsl:apply-templates>
                    </xsl:when>
                    <xsl:otherwise>
                      <xsl:apply-templates select="Question">
                        <xsl:with-param name="lockItem" select="'No'" />
                      </xsl:apply-templates>
                    </xsl:otherwise>
                  </xsl:choose>
                </xsl:when>
                <xsl:otherwise>
                  <xsl:value-of select="@Name" />
                </xsl:otherwise>
              </xsl:choose>
            </div>
          </div>
        </xsl:when>
        <xsl:otherwise> <!-- Not a title -->
          <div class="row gx-5">
            <div class="col-3 border text-right"> <!-- Item lable column -->
              <xsl:choose>
                <xsl:when test="./Question">
                  <xsl:choose>
                    <xsl:when test="$itemCondition != 'null'">
                      &#160;&#160;<span class="material-symbols-outlined alert-green">subdirectory_arrow_right</span>&#160;
                      <xsl:apply-templates select="Question">
                        <xsl:with-param name="lockItem" select="'No'" />
                      </xsl:apply-templates>
                    </xsl:when>
                    <xsl:otherwise>
                      <xsl:apply-templates select="Question">
                        <xsl:with-param name="lockItem" select="//ItemGroupDef/ItemRef[@ItemOID = current()/@OID]/@osb:locked" />
                      </xsl:apply-templates>
                    </xsl:otherwise>
                  </xsl:choose>
                </xsl:when>
                <xsl:otherwise>
                  <xsl:value-of select="@Name" />
                </xsl:otherwise>
              </xsl:choose>
              <xsl:if test="//ItemGroupDef/ItemRef[@ItemOID = current()/@OID]/@Mandatory = 'Yes'">
                <em> * </em>
              </xsl:if>
            </div>
            <!-- Item field column -->
            <xsl:choose>
              <xsl:when test="MeasurementUnitRef">
                <div class="col-5 border text-left">
                  <input type="{@DataType}" class="form-control" id="{@OID}" name="{@Name}" min="4" max="40" size="{@Length}"/>
                </div>
                <div class="col-1 border text-left">
                  Unit :
                </div>
                <div class="col-3 border text-left">
                  <xsl:for-each select="MeasurementUnitRef">
                    <input type="radio" id="{@MeasurementUnitOID}" name="{../@OID}" value="{@MeasurementUnitOID}" />
                    <label for="contactChoice1">&#160;
                      <xsl:apply-templates select="//BasicDefinitions/MeasurementUnit[@OID = current()/@MeasurementUnitOID]/Symbol" />
                    </label><br />
                  </xsl:for-each>
                </div>
              </xsl:when>
              <xsl:otherwise>
                <div class="col-9 border text-left">
                  <xsl:choose>
                    <xsl:when test="CodeListRef">
                      <xsl:for-each select="CodeListRef">
                        <xsl:for-each select="//CodeList[@OID = current()/@CodeListOID]/CodeListItem">
                          <input type="{$displayType}" id="{@CodedValue}" name="{../@OID}" value="{@CodedValue}" />
                          <label for="contactChoice2">&#160;<xsl:apply-templates select="Decode"/></label><br />
                        </xsl:for-each>
                        <xsl:for-each select="//CodeList[@OID = current()/@CodeListOID]/EnumeratedItem">
                          <input type="{$displayType}" id="{@CodedValue}" name="{../@OID}" value="{@CodedValue}" />
                          <label for="contactChoice2">&#160;<xsl:value-of select="@CodedValue" /></label><br />
                        </xsl:for-each>
                      </xsl:for-each>
                    </xsl:when>
                    <xsl:otherwise>
                      <input type="{@DataType}" class="form-control" id="{@OID}" name="{@Name}" min="4" max="40" size="{@Length}"/>
                    </xsl:otherwise>
                  </xsl:choose>
                </div>
              </xsl:otherwise>
            </xsl:choose>
          </div>
        </xsl:otherwise>
      </xsl:choose>
    </div>
  </xsl:template>

  <xsl:template match="ItemGroupDef">
    <div class="alert alert-dark" role="alert">
      <xsl:variable name="domainLevel" select="../FormDef/ItemGroupRef[@ItemGroupOID = current()/@OID]/@OrderNumber+1" />
      <h4>
        <xsl:value-of select="$domainLevel"/>: <xsl:value-of select="@Name" />&#160;
        <xsl:if test="//FormDef/ItemGroupRef[@ItemGroupOID = current()/@OID]/@Mandatory = 'Yes'">
          <em> * </em>
        </xsl:if>
      </h4>
      <xsl:for-each select="ItemRef">
        <xsl:sort select="@OrderNumber"/>
        <xsl:apply-templates select="//ItemDef[@OID = current()/@ItemOID]">
          <xsl:with-param name="domainNiv" select="$domainLevel"/>
          <xsl:with-param name="itemCondition" select="current()/@CollectionExceptionConditionOID"/>
        </xsl:apply-templates>
      </xsl:for-each>
    </div>
  </xsl:template>

  <xsl:template match="FormDef" >
    <ul class="nav nav-tabs">
      <li class="nav-item">
        <a class="nav-link active" href="#"><h2><xsl:value-of select="@Name" /></h2></a>
      </li>
      <li class="nav-item">
        <a class="nav-link disabled" href="#" tabindex="-1" aria-disabled="true"><em>*</em> for mandatory item </a>
      </li>
      <xsl:choose>
        <xsl:when test="Description">
          <li class="nav-item">
            <xsl:apply-templates select="Description"/>
          </li>
        </xsl:when>
      </xsl:choose>
    </ul>
    <xsl:for-each select="ItemGroupRef">
      <xsl:sort select="current()/@OrderNumber"/>
      <xsl:apply-templates select="//ItemGroupDef[@OID = current()/@ItemGroupOID]"/><br />
    </xsl:for-each>
    <br /><br />
  </xsl:template>

  <xsl:template match="Description">
    <span class="online-help">
      <span class="material-symbols-outlined">info</span>
      <xsl:value-of select="TranslatedText" />
    </span>
  </xsl:template>

  <xsl:template match="Question">
    <xsl:param name="lockItem"/>
    <xsl:choose>
      <xsl:when test="$lockItem = 'No'">
        <span class="notLockItem"><xsl:value-of select="TranslatedText" /></span>
      </xsl:when>
      <xsl:otherwise>
        <xsl:value-of select="TranslatedText" />
      </xsl:otherwise>
    </xsl:choose>
  </xsl:template>

  <xsl:template match="Decode">
    <xsl:value-of select="TranslatedText" />
  </xsl:template>

  <xsl:template match="Symbol">
    <xsl:value-of select="TranslatedText" />
  </xsl:template>

  <xsl:template name="splitter">
    <xsl:param name="remaining-string"/>
    <xsl:param name="pattern"/>
    <xsl:choose>
      <xsl:when test="contains($remaining-string,$pattern)">
        <split-item>
          <span class="badge" style="background-color:#bfffff; border: 1px solid #000;">
            <xsl:value-of select = "normalize-space(substring-before($remaining-string,$pattern))"/>
          </span>
        </split-item>
        <xsl:call-template name="splitter">
          <xsl:with-param name="remaining-string"  select="substring-after($remaining-string,$pattern)"/>
          <xsl:with-param name="pattern"  select="$pattern"/>
        </xsl:call-template>
      </xsl:when>
      <xsl:otherwise>
        <split-item>
          <span class="badge" style="background-color:#bfffff; border: 1px solid #000;">
            <xsl:value-of select = "normalize-space($remaining-string)"/>
          </span>
        </split-item>
      </xsl:otherwise>
    </xsl:choose>
  </xsl:template>

</xsl:stylesheet>