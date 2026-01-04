import api from "./client";

export interface DiatonicChord {
  roman_numeral: string;
  chord_name: string;
  degree: number;
  function: string;
  tension: number;
}

export const theoryApi = {
  async getDiatonicChords(projectId: string, includeBorrowed = false): Promise<DiatonicChord[]> {
    const response = await api.get<DiatonicChord[]>(
      `/theory/chords?project_id=${projectId}&include_borrowed=${includeBorrowed}`
    );
    return response.data;
  },
};
