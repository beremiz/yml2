<xsl:stylesheet xmlns:func="http://exslt.org/functions" xmlns:dyn="http://exslt.org/dynamic" xmlns:str="http://exslt.org/strings" xmlns:math="http://exslt.org/math" xmlns:xsl="http://www.w3.org/1999/XSL/Transform" extension-element-prefixes="exsl func str dyn set math" xmlns:set="http://exslt.org/sets" version="1.0" xmlns:exsl="http://exslt.org/common"><xsl:output method="text"/><xsl:variable name="space" select="'                                                                                                                                                                                                        '"/><xsl:param name="autoindent" select="4"/><xsl:template match="/"><xsl:param name="_indent" select="0"/><xsl:value-of select="substring($space, 1, $_indent+0*$autoindent)"/>hello, world
</xsl:template></xsl:stylesheet>
