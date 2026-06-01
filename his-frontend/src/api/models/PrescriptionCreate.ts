/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { PrescriptionItemCreate } from './PrescriptionItemCreate';
export type PrescriptionCreate = {
    registration_id: number;
    pres_type: string;
    diagnosis?: (string | null);
    items: Array<PrescriptionItemCreate>;
};

