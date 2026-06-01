/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
export type AdmissionOut = {
    id: number;
    admission_no: string;
    patient_id: number;
    bed_id: number;
    department_id: number;
    admit_date: string;
    discharge_date: (string | null);
    deposit: string;
    total_fee: string;
    settled: boolean;
};

