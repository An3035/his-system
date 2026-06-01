/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { AiChatRequest } from '../models/AiChatRequest';
import type { AiChatResponse } from '../models/AiChatResponse';
import type { CancelablePromise } from '../core/CancelablePromise';
import { OpenAPI } from '../core/OpenAPI';
import { apiRequest as __request } from '../core/request';

export class AiService {
    /**
     * Ai Chat
     * @param requestBody
     * @returns AiChatResponse Successful Response
     * @throws ApiError
     */
    public static aiChatApiAiChatPost(
        requestBody: AiChatRequest,
    ): CancelablePromise<AiChatResponse> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/api/ai/chat',
            body: requestBody,
            mediaType: 'application/json',
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Summarize Patient
     * @param patientId
     * @returns any Successful Response
     * @throws ApiError
     */
    public static summarizePatientApiAiSummarizePatientPatientIdPost(
        patientId: number,
    ): CancelablePromise<any> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/api/ai/summarize-patient/{patient_id}',
            path: {
                'patient_id': patientId,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Drug Interaction
     * @param requestBody
     * @returns any Successful Response
     * @throws ApiError
     */
    public static drugInteractionApiAiDrugInteractionPost(
        requestBody: Array<string>,
    ): CancelablePromise<any> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/api/ai/drug-interaction',
            body: requestBody,
            mediaType: 'application/json',
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Director Insight
     * @param reportType
     * @returns any Successful Response
     * @throws ApiError
     */
    public static directorInsightApiAiDirectorInsightGet(
        reportType: string = '收入报表',
    ): CancelablePromise<any> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/ai/director-insight',
            query: {
                'report_type': reportType,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
}
