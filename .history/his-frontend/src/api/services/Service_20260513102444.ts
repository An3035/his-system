/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { AdmissionCreate } from '../models/AdmissionCreate';
import type { AdmissionOut } from '../models/AdmissionOut';
import type { BedOut } from '../models/BedOut';
import type { Body_login_api_auth_login_post } from '../models/Body_login_api_auth_login_post';
import type { DashboardStats } from '../models/DashboardStats';
import type { DrugCreate } from '../models/DrugCreate';
import type { DrugOut } from '../models/DrugOut';
import type { InventoryOut } from '../models/InventoryOut';
import type { MedicalOrderCreate } from '../models/MedicalOrderCreate';
import type { MedicalOrderOut } from '../models/MedicalOrderOut';
import type { PatientCreate } from '../models/PatientCreate';
import type { PatientOut } from '../models/PatientOut';
import type { PrescriptionCreate } from '../models/PrescriptionCreate';
import type { PrescriptionOut } from '../models/PrescriptionOut';
import type { RegistrationCreate } from '../models/RegistrationCreate';
import type { RegistrationOut } from '../models/RegistrationOut';
import type { Token } from '../models/Token';
import type { UserOut } from '../models/UserOut';
import type { CancelablePromise } from '../core/CancelablePromise';
import { OpenAPI } from '../core/OpenAPI';
import { apiRequest as __request } from '../core/request';
export class Service {
    /**
     * Login
     * @param formData
     * @returns Token Successful Response
     * @throws ApiError
     */
    public static loginApiAuthLoginPost(
        formData: Body_login_api_auth_login_post,
    ): CancelablePromise<Token> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/api/auth/login',
            formData: formData,
            mediaType: 'application/x-www-form-urlencoded',
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Me
     * @returns UserOut Successful Response
     * @throws ApiError
     */
    public static meApiAuthMeGet(): CancelablePromise<UserOut> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/auth/me',
        });
    }
    /**
     * Create Patient
     * @param requestBody
     * @returns PatientOut Successful Response
     * @throws ApiError
     */
    public static createPatientApiPatientsPost(
        requestBody: PatientCreate,
    ): CancelablePromise<PatientOut> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/api/patients',
            body: requestBody,
            mediaType: 'application/json',
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Search Patients
     * @param q
     * @returns PatientOut Successful Response
     * @throws ApiError
     */
    public static searchPatientsApiPatientsGet(
        q: string = '',
    ): CancelablePromise<Array<PatientOut>> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/patients',
            query: {
                'q': q,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Get Patient
     * @param patientId
     * @returns PatientOut Successful Response
     * @throws ApiError
     */
    public static getPatientApiPatientsPatientIdGet(
        patientId: number,
    ): CancelablePromise<PatientOut> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/patients/{patient_id}',
            path: {
                'patient_id': patientId,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Create Registration
     * @param requestBody
     * @returns RegistrationOut Successful Response
     * @throws ApiError
     */
    public static createRegistrationApiRegistrationsPost(
        requestBody: RegistrationCreate,
    ): CancelablePromise<RegistrationOut> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/api/registrations',
            body: requestBody,
            mediaType: 'application/json',
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * List Registrations
     * @param patientId
     * @param visitDate
     * @returns RegistrationOut Successful Response
     * @throws ApiError
     */
    public static listRegistrationsApiRegistrationsGet(
        patientId?: (number | null),
        visitDate?: (string | null),
    ): CancelablePromise<Array<RegistrationOut>> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/registrations',
            query: {
                'patient_id': patientId,
                'visit_date': visitDate,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Pay Registration
     * @param regId
     * @returns RegistrationOut Successful Response
     * @throws ApiError
     */
    public static payRegistrationApiRegistrationsRegIdPayPatch(
        regId: number,
    ): CancelablePromise<RegistrationOut> {
        return __request(OpenAPI, {
            method: 'PATCH',
            url: '/api/registrations/{reg_id}/pay',
            path: {
                'reg_id': regId,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Create Drug
     * @param requestBody
     * @returns DrugOut Successful Response
     * @throws ApiError
     */
    public static createDrugApiDrugsPost(
        requestBody: DrugCreate,
    ): CancelablePromise<DrugOut> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/api/drugs',
            body: requestBody,
            mediaType: 'application/json',
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * List Drugs
     * @param q
     * @param drugType
     * @returns DrugOut Successful Response
     * @throws ApiError
     */
    public static listDrugsApiDrugsGet(
        q: string = '',
        drugType?: (string | null),
    ): CancelablePromise<Array<DrugOut>> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/drugs',
            query: {
                'q': q,
                'drug_type': drugType,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * List Inventory
     * @param lowStock
     * @param pharmacyType
     * @returns InventoryOut Successful Response
     * @throws ApiError
     */
    public static listInventoryApiPharmacyInventoryGet(
        lowStock: boolean = false,
        pharmacyType?: (string | null),
    ): CancelablePromise<Array<InventoryOut>> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/pharmacy/inventory',
            query: {
                'low_stock': lowStock,
                'pharmacy_type': pharmacyType,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Return Drug
     * 退药：增加库存并记录流水。
     * @param drugId
     * @param quantity
     * @param prescriptionId
     * @returns any Successful Response
     * @throws ApiError
     */
    public static returnDrugApiPharmacyReturnDrugPost(
        drugId: number,
        quantity: (number | string),
        prescriptionId: number,
    ): CancelablePromise<any> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/api/pharmacy/return-drug',
            query: {
                'drug_id': drugId,
                'quantity': quantity,
                'prescription_id': prescriptionId,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Sales Stats
     * 销量统计报表。
     * @param startDate
     * @param endDate
     * @returns any Successful Response
     * @throws ApiError
     */
    public static salesStatsApiPharmacySalesStatsGet(
        startDate: string,
        endDate: string,
    ): CancelablePromise<any> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/pharmacy/sales-stats',
            query: {
                'start_date': startDate,
                'end_date': endDate,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Warehouse Inventory
     * @param warehouseType
     * @returns any Successful Response
     * @throws ApiError
     */
    public static warehouseInventoryApiWarehouseInventoryGet(
        warehouseType?: (string | null),
    ): CancelablePromise<any> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/warehouse/inventory',
            query: {
                'warehouse_type': warehouseType,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Stock In
     * 入库。
     * @param drugId
     * @param quantity
     * @param warehouseType
     * @returns any Successful Response
     * @throws ApiError
     */
    public static stockInApiWarehouseStockInPost(
        drugId: number,
        quantity: (number | string),
        warehouseType: string,
    ): CancelablePromise<any> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/api/warehouse/stock-in',
            query: {
                'drug_id': drugId,
                'quantity': quantity,
                'warehouse_type': warehouseType,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Admit Patient
     * @param requestBody
     * @returns AdmissionOut Successful Response
     * @throws ApiError
     */
    public static admitPatientApiAdmissionsPost(
        requestBody: AdmissionCreate,
    ): CancelablePromise<AdmissionOut> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/api/admissions',
            body: requestBody,
            mediaType: 'application/json',
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Discharge Patient
     * 出院结算。
     * @param admId
     * @returns any Successful Response
     * @throws ApiError
     */
    public static dischargePatientApiAdmissionsAdmIdDischargePatch(
        admId: number,
    ): CancelablePromise<any> {
        return __request(OpenAPI, {
            method: 'PATCH',
            url: '/api/admissions/{adm_id}/discharge',
            path: {
                'adm_id': admId,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Daily Bill
     * 模块8: 一日清单查询。
     * @param admId
     * @param billDate
     * @returns any Successful Response
     * @throws ApiError
     */
    public static dailyBillApiAdmissionsAdmIdDailyBillGet(
        admId: number,
        billDate?: string,
    ): CancelablePromise<any> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/admissions/{adm_id}/daily-bill',
            path: {
                'adm_id': admId,
            },
            query: {
                'bill_date': billDate,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * List Beds
     * @param departmentId
     * @param status
     * @returns BedOut Successful Response
     * @throws ApiError
     */
    public static listBedsApiNurseBedsGet(
        departmentId?: (number | null),
        status?: (string | null),
    ): CancelablePromise<Array<BedOut>> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/nurse/beds',
            query: {
                'department_id': departmentId,
                'status': status,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Create Order
     * @param requestBody
     * @returns MedicalOrderOut Successful Response
     * @throws ApiError
     */
    public static createOrderApiOrdersPost(
        requestBody: MedicalOrderCreate,
    ): CancelablePromise<MedicalOrderOut> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/api/orders',
            body: requestBody,
            mediaType: 'application/json',
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * List Orders
     * @param admissionId
     * @param orderType
     * @returns MedicalOrderOut Successful Response
     * @throws ApiError
     */
    public static listOrdersApiOrdersGet(
        admissionId?: (number | null),
        orderType?: (string | null),
    ): CancelablePromise<Array<MedicalOrderOut>> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/orders',
            query: {
                'admission_id': admissionId,
                'order_type': orderType,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Execute Order
     * @param orderId
     * @returns any Successful Response
     * @throws ApiError
     */
    public static executeOrderApiOrdersOrderIdExecutePatch(
        orderId: number,
    ): CancelablePromise<any> {
        return __request(OpenAPI, {
            method: 'PATCH',
            url: '/api/orders/{order_id}/execute',
            path: {
                'order_id': orderId,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * List Charge Items
     * @param category
     * @returns any Successful Response
     * @throws ApiError
     */
    public static listChargeItemsApiChargesItemsGet(
        category?: (string | null),
    ): CancelablePromise<any> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/charges/items',
            query: {
                'category': category,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Create Special Charge
     * @param orderId
     * @param chargeItemId
     * @param quantity
     * @returns any Successful Response
     * @throws ApiError
     */
    public static createSpecialChargeApiChargesCreatePost(
        orderId: number,
        chargeItemId: number,
        quantity: number = 1,
    ): CancelablePromise<any> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/api/charges/create',
            query: {
                'order_id': orderId,
                'charge_item_id': chargeItemId,
                'quantity': quantity,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Dashboard
     * @returns DashboardStats Successful Response
     * @throws ApiError
     */
    public static dashboardApiDirectorDashboardGet(): CancelablePromise<DashboardStats> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/director/dashboard',
        });
    }
    /**
     * Revenue Report
     * @param startDate
     * @param endDate
     * @returns any Successful Response
     * @throws ApiError
     */
    public static revenueReportApiDirectorRevenueReportGet(
        startDate: string,
        endDate: string,
    ): CancelablePromise<any> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/director/revenue-report',
            query: {
                'start_date': startDate,
                'end_date': endDate,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Query By Ic
     * IC卡查询患者信息及当日就诊记录。
     * @param icCard
     * @returns any Successful Response
     * @throws ApiError
     */
    public static queryByIcApiKioskQueryByIcGet(
        icCard: string,
    ): CancelablePromise<any> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/kiosk/query-by-ic',
            query: {
                'ic_card': icCard,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Drug Prices
     * 药价公开查询（无需登录）。
     * @param q
     * @returns any Successful Response
     * @throws ApiError
     */
    public static drugPricesApiKioskDrugPricesGet(
        q: string = '',
    ): CancelablePromise<any> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/kiosk/drug-prices',
            query: {
                'q': q,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Kiosk Departments
     * 科室介绍（含医生列表）。
     * @returns any Successful Response
     * @throws ApiError
     */
    public static kioskDepartmentsApiKioskDepartmentsGet(): CancelablePromise<any> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/kiosk/departments',
        });
    }
    /**
     * Inpatient Daily Bill
     * 住院患者一日清单（触摸屏自助查询）。
     * @param admissionNo
     * @returns any Successful Response
     * @throws ApiError
     */
    public static inpatientDailyBillApiKioskInpatientDailyBillGet(
        admissionNo: string,
    ): CancelablePromise<any> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/kiosk/inpatient-daily-bill',
            query: {
                'admission_no': admissionNo,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Create Prescription
     * @param requestBody
     * @returns PrescriptionOut Successful Response
     * @throws ApiError
     */
    public static createPrescriptionApiPrescriptionsPost(
        requestBody: PrescriptionCreate,
    ): CancelablePromise<PrescriptionOut> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/api/prescriptions',
            body: requestBody,
            mediaType: 'application/json',
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Pay Prescription
     * 门诊收费 — 支付处方，自动推送至药房发药窗口（模块5）。
     * @param presId
     * @returns PrescriptionOut Successful Response
     * @throws ApiError
     */
    public static payPrescriptionApiPrescriptionsPresIdPayPatch(
        presId: number,
    ): CancelablePromise<PrescriptionOut> {
        return __request(OpenAPI, {
            method: 'PATCH',
            url: '/api/prescriptions/{pres_id}/pay',
            path: {
                'pres_id': presId,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Pending Dispense
     * 模块5: 药房发药窗口 — 获取已付款待发药处方列表。
     * @returns PrescriptionOut Successful Response
     * @throws ApiError
     */
    public static pendingDispenseApiPrescriptionsPendingDispenseGet(): CancelablePromise<Array<PrescriptionOut>> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/prescriptions/pending-dispense',
        });
    }
    /**
     * Dispense Prescription
     * @param presId
     * @returns any Successful Response
     * @throws ApiError
     */
    public static dispensePrescriptionApiPrescriptionsPresIdDispensePatch(
        presId: number,
    ): CancelablePromise<any> {
        return __request(OpenAPI, {
            method: 'PATCH',
            url: '/api/prescriptions/{pres_id}/dispense',
            path: {
                'pres_id': presId,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Root
     * @returns any Successful Response
     * @throws ApiError
     */
    public static rootGet(): CancelablePromise<any> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/',
        });
    }
    /**
     * Health
     * @returns any Successful Response
     * @throws ApiError
     */
    public static healthHealthGet(): CancelablePromise<any> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/health',
        });
    }
}
