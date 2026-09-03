# Technical Appendix

## Query Log
1. **Tool**: applications
   - **Scope**: Global
   - **Outcome**: Identified Shopizer as the target application.
   - **Disposition**: run-returned

2. **Tool**: objects (JPA Entity)
   - **Scope**: Application-wide
   - **Result Count**: 52
   - **Disposition**: run-returned
   - **Notable Entries**:
     - Language (236765), ShoppingCartItem (236759), MerchantConfiguration (236755)

3. **Tool**: objects (Spring Beans)
   - **Scope**: Application-wide
   - **Result Count**: 50+
   - **Disposition**: run-returned
   - **Notable Entries**:
     - OrderTotalServiceImpl (21126), apiAdminAuthenticationEntryPoint (21083)

4. **Tool**: objects (Spring MVC)
   - **Scope**: Application-wide
   - **Result Count**: numerous
   - **Disposition**: run-returned

5. **Tool**: stats
   - **Scope**: Application-wide
   - **Outcome**: Provided technology and interaction stats.
   - **Disposition**: run-returned

6. **Tool**: objects (javax.* -- to jakarta.* migration)
   - **Scope**: Application-wide
   - **Result Count**: 2
   - **Disposition**: run-returned
   - **Entries**:
     - DataSourceBuilder<T extends javax.sql.DataSource> (ID: 3057)

## Appendix Entries (names/ID pairs)
- (Source: CAST MCP — objects: Language / 236765)
- (Source: CAST MCP — objects: ShoppingCartItem / 236759)
- (Source: CAST MCP — objects: OrderTotalServiceImpl / 21126)
- (Source: CAST MCP — stats: LOC 91162, Technologies identified)
- (Source: CAST MCP — objects: DataSourceBuilder / 3057)

**Note**: Shopizer build configuration files weren't found during the analysis session. Further execution assuming presence or tailored strategy based on configurations. Compliance gaps marked where applicable due to missing BCM scope.