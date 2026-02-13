using ITnet2.Server.Session;
using ITnet2.Server.Runtime.Methods;
using System;
using System.Linq;
using System.Net;
using System.IO;
using System.Text;
using Newtonsoft.Json;
using ITnet2.Server.Data;
using ITnet2.Server.Dialogs;
using ITnet2.Server.BusinessLogic.Core.Originals;

public class MyFile
{
    public string FILENAME { get; set; }
    public string CONTENT { get; set; }
}

public static class FileComparison
{
    // Обрізає довгі рядки для виводу в MessageBox
    private static string Short(string s, int max = 1200)
    {
        if (string.IsNullOrEmpty(s)) return s;
        if (s.Length <= max) return s;
        return s.Substring(0, max) + $"... [trimmed, len={s.Length}]";
    }

    public static string Compare(int undog)
    {
        #region Отримання ID файлу договору

        var sqlDogFileID = $@"
SELECT TOP 1 ID
FROM DOR
WHERE TRIM(KDOR) = '{undog}' AND ALIAS = 'DOG' AND FILEEXT = 'DOCX'
ORDER BY ID ASC";

        var resultDogFileID = SqlClient.Main.CreateCommand(sqlDogFileID).ExecObjects(new { ID = "" });
        if (resultDogFileID == null || !resultDogFileID.Any())
        {
            var error = $"Вкладення договору не знайдено";
            InfoManager.MessageBox(error);
            return JsonConvert.SerializeObject(new
            {
                statusCode = 500,
                responseContent = error
            });
        }
        int intDogFileID = Convert.ToInt32(resultDogFileID[0].ID);

        #endregion

        #region apsTenderSql

        var sqlTest = $@"
WITH base AS (
    SELECT dms.undoc, dms.PRC_KOL, dms.KOL_DOP1, dms.KMAT, dms.KOL, dms.EDI,
           dms.CENA_1, dms.SUMMA_1, dms.SUMMA_3, dms.NOM_VM, dms.ORG_DB, dms.kds1,
           dmz.KFPU
    FROM dbo.dog AS dog
    JOIN dbo.dmz AS dmz
      ON dmz.UNDOGDS = dog.UNDOG
    JOIN dbo.dms AS dms
      ON dms.undoc = dmz.undoc
    WHERE dog.undog = {undog}
      AND dms.kdmt  = 'SPECTODOG'
)
SELECT
    ksm1.NMAT   AS itemName,
    b.KOL       AS quantity,
    tapei1.NEDI AS unit,
    b.PRC_KOL   AS guaranteeMonths,
    b.KOL_DOP1  AS deliveryPeriod,
    b.CENA_1    AS cena,
    b.SUMMA_1   AS summa,
    ISNULL(b.SUMMA_1,0) + ISNULL(b.SUMMA_3,0) AS contractTotal,
    b.KFPU      AS paymentTermsCode,
    fpu1.NFPU_S AS paymentTermsTitleShort,
    b.NOM_VM    AS incoterms,
    country1.NAIM AS country,
    org1.NORG     AS orgName,
    CONCAT(dlv1.NAIM, ' ', dlv1.CHAR_SP4) AS deliveryAddress
FROM base AS b
OUTER APPLY (SELECT TOP (1) d.* FROM dbo.dmsadd_ AS d WHERE d.undoc = b.undoc) dmsadd1
OUTER APPLY (SELECT TOP (1) s.NAIM FROM dbo.sp2 AS s WHERE s.SPR = 'RES' AND RTRIM(s.KOD_N)=RTRIM(dmsadd1.KRES)) country1
OUTER APPLY (SELECT TOP (1) s.NAIM, s.CHAR_SP4 FROM dbo.sp2 AS s WHERE s.SPR='_DLVPL' AND RTRIM(s.KOD_C)=RTRIM(b.kds1)) dlv1
OUTER APPLY (SELECT TOP (1) k.NMAT FROM dbo.ksm AS k WHERE k.KMAT = b.KMAT) ksm1
OUTER APPLY (SELECT TOP (1) t.NEDI FROM dbo.tapei AS t WHERE t.edi = b.EDI) tapei1
OUTER APPLY (SELECT TOP (1) o.NORG FROM dbo.org AS o WHERE o.org = b.ORG_DB) org1
OUTER APPLY (SELECT TOP (1) f.NFPU_S FROM dbo.fpu AS f WHERE f.kfpu = b.KFPU) fpu1;
";

        var resultTestSql = SqlClient.Main.CreateCommand(sqlTest).ExecObjects(new
        {
            itemName = "",
            quantity = "",
            unit = "",
            guaranteeMonths = "",
            deliveryPeriod = "",
            cena = "",
            summa = "",
            contractTotal = "",
            paymentTermsCode = "",
            paymentTermsTitleShort = "",
            incoterms = "",
            country = "",
            orgName = "",
            deliveryAddress = ""
        });

        int testRecordsCount = resultTestSql?.Count ?? 0;

        if (testRecordsCount > 0)
        {
            var file1 = Originals.ExportFile(intDogFileID);
            string exportedFilePath1 = file1.FilePath;
            string exportedFileName1 = file1.FileName;
            byte[] exportedFileBytes1 = File.ReadAllBytes(exportedFilePath1);

            string jsonRequirements = JsonConvert.SerializeObject(resultTestSql);

            FileUploader2 uploader2 = new FileUploader2("http://192.168.210.36:7070/upload-json");
            (HttpStatusCode statusCode, string responseContent) = uploader2.UploadFileAndJson(
              fileBytes: exportedFileBytes1,
              fileName: exportedFileName1,
              jsonRequirements: jsonRequirements
            );

            var jsonObj = new
            {
                statusCode = statusCode,
                responseContent = responseContent
            };
            string jsonResult = JsonConvert.SerializeObject(jsonObj);

            return jsonResult;
        }

        #endregion

        #region Отримання ID тендеру

        string tenderID = null;
        int intTenderID = 0;

        var sqlTenderID = $@"
SELECT TOP 1 SLUZH_Z_.UNDOC
FROM DOG
LEFT JOIN dmz ON (dmz.undog = dog.undog OR dmz.undogds = dog.undog) AND dmz.kdmt='purchorder'
LEFT JOIN SLUZH_O_ ON SLUZH_O_.UNDOC_DB = dmz.UNDOC 
LEFT JOIN SLUZH_Z_ ON SLUZH_Z_.UNDOC   = SLUZH_O_.UNDOC_CR
WHERE dog.undog = {undog} OR dog.undog_pr = {undog}";

        var resultTenderID = SqlClient.Main.CreateCommand(sqlTenderID).ExecObjects(new { UNDOC = "" });

        if (resultTenderID == null || !resultTenderID.Any() || (resultTenderID[0]?.UNDOC?.ToString() == "0"))
        {
            string stubSql = @"
SELECT SP.UNDOC AS UNDOC_SP,
       SKV.OVAL,
       SP.SUMMA_1VAL AS SUM1,
       SP.SUMMA_1VAL+SP.SUMMA_3VAL AS SUM_W_VAT,
       DOP.KDGPS,
       T.UNDOC AS UN_TEND,
       T.COMM AS COMM_TEND
FROM DMZ SP
LEFT JOIN DOG DOP ON DOP.UNDOG = SP.UNDOGDS
LEFT JOIN SKV ON SKV.KVAL = SP.KVAL
LEFT JOIN DMZ P ON EXISTS(
    SELECT 1 FROM DMZO
    WHERE DMZO.UNDMTP = 177
      AND DMZO.UNDOC_DB = P.UNDOC
      AND DMZO.UNDOC_CR = SP.UNDOC)
LEFT JOIN SLUZH_Z_ T ON EXISTS(
    SELECT 1 FROM SLUZH_O_
    WHERE SLUZH_O_.ALIAS_DB = 'DMS'
      AND SLUZH_O_.UNDOC_DB = P.UNDOC
      AND SLUZH_O_.ALIAS_CR = 'SLUZH_S_'
      AND SLUZH_O_.UNDOC_CR = T.UNDOC)
WHERE SP.KDMT LIKE 'SPEC%' AND SP.UNDOG=@UNDOG";

            var tempTable = SqlClient.Main
                .CreateCommand(stubSql, new SqlParam("UNDOG", undog))
                .LoadToLocalDb();

            if (!SqlClient.Local.RecordsExist(tempTable))
            {
                var error = "Тендер не знайдено";
                InfoManager.MessageBox(error);
                SqlClient.Local.DropTempTable(tempTable);
                return JsonConvert.SerializeObject(new
                {
                    statusCode = 500,
                    responseContent = error
                });
            }

            using (var cursor = new GridCursor(tempTable))
            {
                var selector = new RowSelector(cursor)
                {
                    Caption = "Вибір тендеру для порівняння",
                    GridWidth = 300
                };
                selector.Grid.Columns.Add("UN_TEND", "№ тендеру");
                selector.Grid.Columns.Add("COMM_TEND", "Зміст тендеру");
                selector.Grid.Columns.Add("UNDOC_SP", "Унік.№ спец.");
                selector.Grid.Columns.Add("OVAL", "Вал.");
                selector.Grid.Columns.Add("SUM1", "Сума без ПДВ");
                selector.Grid.Columns.Add("SUM_W_VAT", "Сума з ПДВ");
                selector.Grid.Columns.Add("KDGPS", "№ дод. угоди");

                if (selector.Activate())
                {
                    intTenderID = cursor.GetFieldValue<int>("UN_TEND");
                    tenderID = intTenderID.ToString();
                }
            }

            SqlClient.Local.DropTempTable(tempTable);
        }
        else
        {
            tenderID = resultTenderID[0].UNDOC.ToString();
            intTenderID = Convert.ToInt32(resultTenderID[0].UNDOC);
        }

        #endregion

        #region Отримання ID файлу тендеру

        var sqlTenderFileID = $@"
SELECT ID
FROM DOR
WHERE TRIM(KDOR) = '{tenderID}' AND ALIAS = 'SLUZH_Z_' AND KDRV = 'PR_'";

        var resultTenderFileID = SqlClient.Main.CreateCommand(sqlTenderFileID).ExecObjects(new { ID = "" });
        if (resultTenderFileID == null || !resultTenderFileID.Any())
        {
            var ci = new DataEditor.StartInfo("_UMT10_NIB");
            ci.StartMode = new DataEditor.StartInfo.DataEditorStartMode(
                new DataEditor.StartInfo.RrtStartMode(DataEditor.StartInfo.RrtStartMode.MethodType.Document, "_GEN_PR")
                { ExitAfterCall = true }
            );
            ci.CustomProperties.Add("PROPCALL", "+");
            ci.AdditionalFilter = new SqlCmdText("SLUZH_Z_.UNDOC=@UNDOC", new SqlParam("UNDOC", intTenderID));
            DataEditor.Call(ci);

            resultTenderFileID = SqlClient.Main.CreateCommand(sqlTenderFileID).ExecObjects(new { ID = "" });
            if (resultTenderFileID == null || !resultTenderFileID.Any())
            {
                var error = "Вкладення тендеру не знайдено навіть після генерації";
                InfoManager.MessageBox(error);
                return JsonConvert.SerializeObject(new
                {
                    statusCode = 500,
                    responseContent = error
                });
            }
        }
        int intTenderFileID = Convert.ToInt32(resultTenderFileID[0].ID);

        #endregion

        #region Завантаження файлів

        var file1_ = Originals.ExportFile(intDogFileID);
        string exportedFilePath1_ = file1_.FilePath;
        string exportedFileName1_ = file1_.FileName;
        byte[] exportedFileBytes1_ = File.ReadAllBytes(exportedFilePath1_);

        var file2 = Originals.ExportFile(intTenderFileID);
        string exportedFilePath2 = file2.FilePath;
        string exportedFileName2 = file2.FileName;
        byte[] exportedFileBytes2 = File.ReadAllBytes(exportedFilePath2);

        #endregion

        #region Вiдправка файлів

        FileUploader uploader = new FileUploader("http://192.168.210.36:7070/upload");
        (HttpStatusCode statusCode2, string responseContent2) = uploader.UploadFiles(
          fileBytes1: exportedFileBytes1_,
          fileBytes2: exportedFileBytes2,
          fileName1: exportedFileName1_,
          fileName2: exportedFileName2
        );

        #endregion

        #region Повернення результату

        var jsonObj2 = new
        {
            statusCode = statusCode2,
            responseContent = responseContent2
        };
        string jsonResult2 = JsonConvert.SerializeObject(jsonObj2);
        return jsonResult2;

        #endregion
    }

    // Витягує структуровані дані з вкладення документа через OCR API.
    // undoc    — унікальний номер документа
    // alias    — тип вкладення в таблиці DOR (наприклад 'AC_SUP')
    // ocrUrl   — адреса OCR ендпоінту
    // fieldsJson — JSON-схема полів для витягнення; якщо null — використовується шаблон за замовчуванням
    // debug    — виводити покроковий лог через InfoManager.MessageBox
    public static string OcrExtract(
        int undoc,
        string alias,
        string ocrUrl,
        string fieldsJson,
        bool debug
    )
    {
        string stage = "START";

        try
        {
            if (debug) InfoManager.MessageBox($"[OCR] ✅ START\r\nUNDOC={undoc}\r\nALIAS={alias}");
            if (debug) InfoManager.MessageBox($"[OCR] URL={ocrUrl}");

            stage = "SQL: FIND DOR.ID";
            var sqlFileId = $@"
SELECT TOP 1 ID, FILEEXT, FILENAME
FROM DOR
WHERE TRIM(KDOR) = '{undoc}'
  AND ALIAS = '{alias}'
  AND FILEEXT IN ('PDF','PNG','JPG','JPEG','TIFF','TIF','DOC','DOCX','XLS','XLSX')
ORDER BY ID ASC";

            if (debug) InfoManager.MessageBox($"[OCR] ▶ Stage={stage}\r\nSQL:\r\n{sqlFileId}");

            var r = SqlClient.Main.CreateCommand(sqlFileId).ExecObjects(new { ID = "", FILEEXT = "", FILENAME = "" });
            if (r == null || !r.Any())
            {
                var error = $"[OCR] ❌ Вкладення не знайдено. UNDOC={undoc}, ALIAS={alias}";
                InfoManager.MessageBox(error);
                return JsonConvert.SerializeObject(new { statusCode = 500, responseContent = error });
            }

            int dorId = Convert.ToInt32(r[0].ID);
            string fileExt = (r[0].FILEEXT ?? "").ToString();
            string fileNameDb = (r[0].FILENAME ?? "").ToString();
            if (debug) InfoManager.MessageBox($"[OCR] ✅ Found attachment\r\nDOR.ID={dorId}\r\nFILEEXT={fileExt}\r\nDB-FILENAME={fileNameDb}");

            stage = "EXPORT: Originals.ExportFile";
            if (debug) InfoManager.MessageBox($"[OCR] ▶ Stage={stage}\r\nExporting DOR.ID={dorId}");
            var f = Originals.ExportFile(dorId);
            if (debug) InfoManager.MessageBox($"[OCR] ✅ Exported\r\nFileName={f.FileName}\r\nFilePath={f.FilePath}");

            stage = "IO: ReadAllBytes";
            if (debug) InfoManager.MessageBox($"[OCR] ▶ Stage={stage}");
            byte[] fileBytes = File.ReadAllBytes(f.FilePath);
            if (debug) InfoManager.MessageBox($"[OCR] ✅ Read bytes\r\nSize={(fileBytes == null ? 0 : fileBytes.Length)} bytes");

            stage = "BUILD: fields JSON";
            if (debug) InfoManager.MessageBox($"[OCR] ▶ Stage={stage}");

            if (string.IsNullOrWhiteSpace(fieldsJson))
            {
                fieldsJson = BuildDefaultFieldsJson();
                if (debug) InfoManager.MessageBox("[OCR] ℹ fieldsJson not provided -> using default template");
            }

            if (debug) InfoManager.MessageBox($"[OCR] ✅ fields JSON (preview):\r\n{Short(fieldsJson, 2000)}");

            stage = "HTTP: Upload multipart (file + fields)";
            if (debug) InfoManager.MessageBox($"[OCR] ▶ Stage={stage}");

            var uploader = new OcrUploader(ocrUrl, debug);
            (HttpStatusCode statusCode, string responseContent) =
                uploader.UploadFileAndFields(fileBytes, f.FileName, fieldsJson);

            if (debug) InfoManager.MessageBox($"[OCR] ✅ Response received\r\nHTTP={(int)statusCode} {statusCode}\r\nBody preview:\r\n{Short(responseContent, 2500)}");

            stage = "RETURN";
            if (debug) InfoManager.MessageBox($"[OCR] ▶ Stage={stage}\r\nReturning result...");

            return JsonConvert.SerializeObject(new
            {
                statusCode = statusCode,
                responseContent = responseContent
            });
        }
        catch (Exception ex)
        {
            var err = $"[OCR] 💥 EXCEPTION\r\nStage={stage}\r\n{ex}";
            InfoManager.MessageBox(err);
            return JsonConvert.SerializeObject(new
            {
                statusCode = 500,
                responseContent = err
            });
        }
    }

    // Шаблон fields за замовчуванням — структура рахунку/накладної
    private static string BuildDefaultFieldsJson()
    {
        var fields = new
        {
            merchant_name = new { type = "str", description = "Name of the merchant/store", required = true },
            total = new { type = "float", description = "Total amount paid", required = true },
            date = new { type = "str", description = "Transaction date", required = true },
            payment_method = new { type = "str", description = "Payment method used", required = false },
            line_items = new
            {
                type = "list[dict]",
                description = "List of items with name, quantity, and price",
                required = true,
                items = new
                {
                    quantity = new { type = "int", description = "Quantity", required = true },
                    service_name = new { type = "str", description = "Service name", required = true },
                    price = new { type = "float", description = "Price", required = true },
                    unit_price = new { type = "float", description = "Unit price", required = true },
                    adjust = new { type = "float", description = "Adjustment amount", required = true },
                    sub_total = new { type = "float", description = "Subtotal amount", required = true }
                }
            }
        };

        return JsonConvert.SerializeObject(fields);
    }

    // Відправляє два файли (doc1, doc2) на /upload
    public class FileUploader
    {
        private string _url;
        public FileUploader(string url)
        {
            _url = url;
        }

        public (HttpStatusCode StatusCode, string ResponseContent) UploadFiles(byte[] fileBytes1, byte[] fileBytes2, string fileName1, string fileName2)
        {
            string boundary = "---------------------------" + DateTime.Now.Ticks.ToString("x");
            HttpWebRequest request = (HttpWebRequest)WebRequest.Create(_url);
            request.ContentType = "multipart/form-data; boundary=" + boundary;
            request.Method = "POST";
            request.Accept = "application/json";

            using (MemoryStream ms = new MemoryStream())
            {
                string contentType1 = GetContentType(fileName1);
                WriteMultipartFormFileData(ms, boundary, "doc1", fileName1, contentType1, fileBytes1);

                string contentType2 = GetContentType(fileName2);
                WriteMultipartFormFileData(ms, boundary, "doc2", fileName2, contentType2, fileBytes2);

                byte[] boundaryEnd = Encoding.ASCII.GetBytes("--" + boundary + "--\r\n");
                ms.Write(boundaryEnd, 0, boundaryEnd.Length);
                ms.Position = 0;
                using (Stream requestStream = request.GetRequestStream())
                {
                    ms.CopyTo(requestStream);
                }
            }
            try
            {
                using (HttpWebResponse response = (HttpWebResponse)request.GetResponse())
                using (Stream responseStream = response.GetResponseStream())
                using (StreamReader reader = new StreamReader(responseStream))
                {
                    string responseString = reader.ReadToEnd();
                    return (response.StatusCode, responseString);
                }
            }
            catch (WebException ex)
            {
                if (ex.Response != null)
                {
                    HttpWebResponse errorResponse = (HttpWebResponse)ex.Response;
                    using (Stream errorStream = errorResponse.GetResponseStream())
                    using (StreamReader reader = new StreamReader(errorStream))
                    {
                        string errorResponseString = reader.ReadToEnd();
                        return (errorResponse.StatusCode, errorResponseString);
                    }
                }
                else
                {
                    return (HttpStatusCode.ServiceUnavailable, ex.Message);
                }
            }
        }

        private static void WriteMultipartFormFileData(Stream stream, string boundary, string fieldName, string fileName, string contentType, byte[] fileData)
        {
            string headerTemplate =
              "--{0}\r\n" +
              "Content-Disposition: form-data; name=\"{1}\"; filename=\"{2}\"\r\n" +
              "Content-Type: {3}\r\n\r\n";

            string header = string.Format(headerTemplate, boundary, fieldName, fileName, contentType);
            byte[] headerBytes = Encoding.UTF8.GetBytes(header);
            stream.Write(headerBytes, 0, headerBytes.Length);

            stream.Write(fileData, 0, fileData.Length);

            byte[] lineBreak = Encoding.ASCII.GetBytes("\r\n");
            stream.Write(lineBreak, 0, lineBreak.Length);
        }

        public static string GetContentType(string filePath)
        {
            string extension = Path.GetExtension(filePath).ToLowerInvariant();
            switch (extension)
            {
                case ".docx":
                    return "application/vnd.openxmlformats-officedocument.wordprocessingml.document";
                case ".doc":
                    return "application/msword";
                case ".xls":
                    return "application/vnd.ms-excel";
                case ".xlsx":
                    return "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet";
                case ".pdf":
                    return "application/pdf";
                case ".png":
                    return "image/png";
                case ".jpg":
                case ".jpeg":
                    return "image/jpeg";
                case ".tif":
                case ".tiff":
                    return "image/tiff";
                default:
                    return "application/octet-stream";
            }
        }
    }

    // Відправляє один файл (doc2) та JSON (requirements) на /upload-json
    public class FileUploader2
    {
        private string _url;
        public FileUploader2(string url)
        {
            _url = url;
        }
        public (HttpStatusCode StatusCode, string ResponseContent) UploadFileAndJson(byte[] fileBytes, string fileName, string jsonRequirements)
        {
            string boundary = "---------------------------" + DateTime.Now.Ticks.ToString("x");
            HttpWebRequest request = (HttpWebRequest)WebRequest.Create(_url);
            request.ContentType = "multipart/form-data; boundary=" + boundary;
            request.Method = "POST";
            request.Accept = "application/json";

            using (MemoryStream ms = new MemoryStream())
            {
                string jsonHeader = $"--{boundary}\r\n" +
                                    "Content-Disposition: form-data; name=\"requirements\"\r\n\r\n";
                byte[] jsonHeaderBytes = Encoding.UTF8.GetBytes(jsonHeader);
                ms.Write(jsonHeaderBytes, 0, jsonHeaderBytes.Length);
                byte[] jsonBytes = Encoding.UTF8.GetBytes(jsonRequirements ?? "");
                ms.Write(jsonBytes, 0, jsonBytes.Length);
                byte[] lineBreak = Encoding.ASCII.GetBytes("\r\n");
                ms.Write(lineBreak, 0, lineBreak.Length);

                string contentType = FileUploader.GetContentType(fileName);
                string fileHeader = $"--{boundary}\r\n" +
                                    $"Content-Disposition: form-data; name=\"doc2\"; filename=\"{fileName}\"\r\n" +
                                    $"Content-Type: {contentType}\r\n\r\n";
                byte[] fileHeaderBytes = Encoding.UTF8.GetBytes(fileHeader);
                ms.Write(fileHeaderBytes, 0, fileHeaderBytes.Length);
                ms.Write(fileBytes, 0, fileBytes.Length);
                ms.Write(lineBreak, 0, lineBreak.Length);

                byte[] boundaryEnd = Encoding.ASCII.GetBytes("--" + boundary + "--\r\n");
                ms.Write(boundaryEnd, 0, boundaryEnd.Length);
                ms.Position = 0;
                using (Stream requestStream = request.GetRequestStream())
                {
                    ms.CopyTo(requestStream);
                }
            }
            try
            {
                using (HttpWebResponse response = (HttpWebResponse)request.GetResponse())
                using (Stream responseStream = response.GetResponseStream())
                using (StreamReader reader = new StreamReader(responseStream))
                {
                    string responseString = reader.ReadToEnd();
                    return (response.StatusCode, responseString);
                }
            }
            catch (WebException ex)
            {
                if (ex.Response != null)
                {
                    HttpWebResponse errorResponse = (HttpWebResponse)ex.Response;
                    using (Stream errorStream = errorResponse.GetResponseStream())
                    using (StreamReader reader = new StreamReader(errorStream))
                    {
                        string errorResponseString = reader.ReadToEnd();
                        return (errorResponse.StatusCode, errorResponseString);
                    }
                }
                else
                {
                    return (HttpStatusCode.ServiceUnavailable, ex.Message);
                }
            }
        }
    }

    // Відправляє один файл (file) та JSON-схему полів (fields) на OCR ендпоінт.
    // Short() викликається як FileComparison.Short() — вкладений клас не має прямого доступу до методів зовнішнього.
    public class OcrUploader
    {
        private readonly string _url;
        private readonly bool _debug;

        public OcrUploader(string url, bool debug)
        {
            _url = url;
            _debug = debug;
        }

        public (HttpStatusCode StatusCode, string ResponseContent) UploadFileAndFields(
            byte[] fileBytes,
            string fileName,
            string fieldsJson
        )
        {
            string stage = "HTTP:INIT";
            string boundary = "---------------------------" + DateTime.Now.Ticks.ToString("x");

            try
            {
                stage = "HTTP:CREATE REQUEST";
                if (_debug) InfoManager.MessageBox($"[OCR-HTTP] ▶ {stage}\r\nBoundary={boundary}");

                HttpWebRequest request = (HttpWebRequest)WebRequest.Create(_url);
                request.Method = "POST";
                request.Accept = "application/json";
                request.ContentType = "multipart/form-data; boundary=" + boundary;

                request.Timeout = 5 * 60 * 1000;
                request.ReadWriteTimeout = 5 * 60 * 1000;
                request.ServicePoint.Expect100Continue = false;

                using (MemoryStream ms = new MemoryStream())
                {
                    stage = "HTTP:WRITE file";
                    string contentType = FileUploader.GetContentType(fileName);
                    if (_debug) InfoManager.MessageBox($"[OCR-HTTP] ▶ {stage}\r\nfileName={fileName}\r\ncontentType={contentType}\r\nbytes={(fileBytes == null ? 0 : fileBytes.Length)}");
                    WriteMultipartFormFileData(ms, boundary, "file", fileName, contentType, fileBytes);

                    stage = "HTTP:WRITE fields";
                    if (_debug) InfoManager.MessageBox(
                        $"[OCR-HTTP] ▶ {stage}\r\nfields preview:\r\n{FileComparison.Short(fieldsJson, 1500)}"
                    );
                    WriteMultipartFormTextData(ms, boundary, "fields", fieldsJson ?? "");

                    stage = "HTTP:END boundary";
                    byte[] boundaryEnd = Encoding.ASCII.GetBytes("--" + boundary + "--\r\n");
                    ms.Write(boundaryEnd, 0, boundaryEnd.Length);

                    stage = "HTTP:SEND";
                    if (_debug) InfoManager.MessageBox($"[OCR-HTTP] ▶ {stage}\r\npayload={ms.Length} bytes");
                    ms.Position = 0;
                    using (Stream requestStream = request.GetRequestStream())
                    {
                        ms.CopyTo(requestStream);
                    }
                }

                stage = "HTTP:GET RESPONSE";
                if (_debug) InfoManager.MessageBox($"[OCR-HTTP] ▶ {stage}");

                using (HttpWebResponse response = (HttpWebResponse)request.GetResponse())
                using (Stream responseStream = response.GetResponseStream())
                using (StreamReader reader = new StreamReader(responseStream))
                {
                    string responseString = reader.ReadToEnd();
                    if (_debug) InfoManager.MessageBox(
                        $"[OCR-HTTP] ✅ OK\r\nHTTP={(int)response.StatusCode} {response.StatusCode}\r\nBody:\r\n{FileComparison.Short(responseString, 2500)}"
                    );
                    return (response.StatusCode, responseString);
                }
            }
            catch (WebException ex)
            {
                if (_debug) InfoManager.MessageBox($"[OCR-HTTP] 💥 WEBEXCEPTION\r\nStage={stage}\r\n{ex.Message}");

                if (ex.Response != null)
                {
                    HttpWebResponse errorResponse = (HttpWebResponse)ex.Response;
                    using (Stream errorStream = errorResponse.GetResponseStream())
                    using (StreamReader reader = new StreamReader(errorStream))
                    {
                        string errorResponseString = reader.ReadToEnd();
                        if (_debug) InfoManager.MessageBox(
                            $"[OCR-HTTP] ❌ ERROR\r\nHTTP={(int)errorResponse.StatusCode} {errorResponse.StatusCode}\r\nBody:\r\n{FileComparison.Short(errorResponseString, 4000)}"
                        );
                        return (errorResponse.StatusCode, errorResponseString);
                    }
                }

                return (HttpStatusCode.ServiceUnavailable, ex.Message);
            }
            catch (Exception ex)
            {
                if (_debug) InfoManager.MessageBox($"[OCR-HTTP] 💥 EXCEPTION\r\nStage={stage}\r\n{ex}");
                return (HttpStatusCode.InternalServerError, ex.ToString());
            }
        }

        // Текстове поле multipart без Content-Type — сервер отримує значення як plain string
        private static void WriteMultipartFormTextData(Stream stream, string boundary, string fieldName, string text)
        {
            string header =
                $"--{boundary}\r\n" +
                $"Content-Disposition: form-data; name=\"{fieldName}\"\r\n" +
                "\r\n";

            byte[] headerBytes = Encoding.UTF8.GetBytes(header);
            stream.Write(headerBytes, 0, headerBytes.Length);

            byte[] textBytes = Encoding.UTF8.GetBytes(text ?? "");
            stream.Write(textBytes, 0, textBytes.Length);

            byte[] lineBreak = Encoding.ASCII.GetBytes("\r\n");
            stream.Write(lineBreak, 0, lineBreak.Length);
        }

        private static void WriteMultipartFormFileData(Stream stream, string boundary, string fieldName, string fileName, string contentType, byte[] fileData)
        {
            string header =
                $"--{boundary}\r\n" +
                $"Content-Disposition: form-data; name=\"{fieldName}\"; filename=\"{fileName}\"\r\n" +
                $"Content-Type: {contentType}\r\n\r\n";

            byte[] headerBytes = Encoding.UTF8.GetBytes(header);
            stream.Write(headerBytes, 0, headerBytes.Length);

            stream.Write(fileData, 0, fileData.Length);

            byte[] lineBreak = Encoding.ASCII.GetBytes("\r\n");
            stream.Write(lineBreak, 0, lineBreak.Length);
        }
    }
}
