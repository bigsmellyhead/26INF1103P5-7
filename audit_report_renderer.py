from sections import ReportSection
from Data import ResultAuditData
class AuditReportRenderer:
    __sections: list[ReportSection]

    def __init__(self, sections):
        self.__sections = sections

    def add_section(self, section):
        self.__sections.append(section)

    def render_sections(self, data: ResultAuditData):
        for section in self.__sections:
            section.render(data)