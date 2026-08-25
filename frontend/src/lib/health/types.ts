export interface HealthResponse
{
    database:       string;
    version:        string;
    uptime_seconds: number;
    environment:    string;
}