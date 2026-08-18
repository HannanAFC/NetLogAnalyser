export type DataExportStatusEnum = 'PENDING' | 'READY' | 'FAILED';

export type DataExportTriggeredByEnum = 'MANUAL' | 'RETENTION_JOB';

export interface DataExport
{
    id:                 string;
    status:             DataExportStatusEnum;
    triggered_by:       DataExportTriggeredByEnum;
    file_size_bytes:    number | null;
    created_at:         string;
    expires_at:         string;
    purged_at:          string | null;
    last_downloaded_at: string | null;
}

export interface GetDataExportsResponse
{
    rows: Array< DataExport >;
}

export interface CreateDataExportResponse
{
    id:         string;
    status:     DataExportStatusEnum;
    created_at: string;
}

export interface GetDataExportDownloadLinkResponse
{
    download_url: string;
}